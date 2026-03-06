"""
Drop-in wrapper for the ``google-genai`` SDK (the unified Gemini SDK)
that auto-evaluates every generation via RAIL Score.

Uses the current ``google-genai`` pattern:
    ``client.models.generate_content(model=..., contents=...)``

Usage:
    from rail_score_sdk.integrations import RAILGemini

    client = RAILGemini(
        gemini_api_key="AIza...",
        rail_api_key="rail_xxx",
        rail_threshold=7.0,
    )

    response = await client.generate(
        model="gemini-2.5-flash",
        contents="Explain quantum computing in simple terms.",
    )
    print(response.content)
    print(response.rail_score)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from rail_score_sdk.async_client import AsyncRAILClient
from rail_score_sdk.policies import EvalResult, Policy, PolicyEngine


@dataclass
class RAILGeminiResponse:
    """Enriched response returned by ``RAILGemini``."""

    content: str
    rail_score: float
    rail_confidence: float
    rail_dimensions: Dict[str, Any]
    rail_issues: List[Dict[str, Any]]
    threshold_met: bool
    was_regenerated: bool
    original_content: Optional[str]
    gemini_response: Any = None
    model: str = ""
    usage: Dict[str, int] = field(default_factory=dict)


class RAILGemini:
    """
    Wraps the ``google-genai`` async client with RAIL evaluation.

    Parameters
    ----------
    gemini_api_key : str, optional
        Gemini API key. Can also be set via ``GEMINI_API_KEY`` env var.
    vertexai : bool
        Use Vertex AI instead of Gemini Developer API.
    project : str, optional
        Google Cloud project ID (required for Vertex AI).
    location : str, optional
        Google Cloud region (required for Vertex AI).
    rail_api_key : str
        RAIL Score API key.
    rail_threshold : float
        Minimum acceptable RAIL score.
    rail_policy : str or Policy
        Enforcement policy.
    rail_mode : str
        ``"basic"`` or ``"deep"``.
    rail_domain : str
        Content domain.
    rail_base_url : str
        Override the RAIL API base URL.
    """

    def __init__(
        self,
        rail_api_key: str,
        *,
        gemini_api_key: Optional[str] = None,
        vertexai: bool = False,
        project: Optional[str] = None,
        location: Optional[str] = None,
        rail_threshold: float = 7.0,
        rail_policy: str | Policy = Policy.LOG_ONLY,
        rail_mode: str = "basic",
        rail_domain: str = "general",
        rail_base_url: str = "https://api.responsibleailabs.ai",
    ) -> None:
        try:
            from google import genai
        except ImportError as exc:
            raise ImportError(
                "The `google-genai` package is required. "
                "Install: pip install google-genai"
            ) from exc

        # Build google-genai Client
        client_kwargs: Dict[str, Any] = {}
        if gemini_api_key:
            client_kwargs["api_key"] = gemini_api_key
        if vertexai:
            client_kwargs["vertexai"] = True
            if project:
                client_kwargs["project"] = project
            if location:
                client_kwargs["location"] = location

        self._genai_client = genai.Client(**client_kwargs)
        # The async interface is via client.aio
        self._aio = self._genai_client.aio

        self._rail = AsyncRAILClient(api_key=rail_api_key, base_url=rail_base_url)
        self._policy = PolicyEngine(policy=rail_policy, threshold=rail_threshold)
        self._mode = rail_mode
        self._domain = rail_domain

    async def generate(
        self,
        *,
        model: str,
        contents: Union[str, List[Any]],
        config: Optional[Any] = None,
        rail_mode: Optional[str] = None,
        rail_skip: bool = False,
        **genai_kwargs: Any,
    ) -> RAILGeminiResponse:
        """
        Generate content and auto-evaluate via RAIL.

        Parameters
        ----------
        model : str
            Gemini model name (e.g. ``"gemini-2.5-flash"``).
        contents : str or list
            Prompt text or structured content parts.
        config : optional
            ``types.GenerateContentConfig`` or dict with generation config.
        rail_mode : str, optional
            Override RAIL mode for this call.
        rail_skip : bool
            Skip RAIL evaluation.
        **genai_kwargs
            Extra args forwarded to ``generate_content``.
        """
        # 1) Call Google GenAI (async)
        gen_kwargs: Dict[str, Any] = {
            "model": model,
            "contents": contents,
            **genai_kwargs,
        }
        if config is not None:
            gen_kwargs["config"] = config

        gemini_response = await self._aio.models.generate_content(**gen_kwargs)

        # Extract text
        content = gemini_response.text or ""

        # Extract usage metadata
        usage = {}
        if hasattr(gemini_response, "usage_metadata") and gemini_response.usage_metadata:
            um = gemini_response.usage_metadata
            usage = {
                "prompt_tokens": getattr(um, "prompt_token_count", 0),
                "candidates_tokens": getattr(um, "candidates_token_count", 0),
                "total_tokens": getattr(um, "total_token_count", 0),
            }

        if rail_skip:
            return RAILGeminiResponse(
                content=content,
                rail_score=0.0,
                rail_confidence=0.0,
                rail_dimensions={},
                rail_issues=[],
                threshold_met=True,
                was_regenerated=False,
                original_content=None,
                gemini_response=gemini_response,
                model=model,
                usage=usage,
            )

        # 2) RAIL evaluation
        effective_mode = rail_mode or self._mode
        context_str = contents if isinstance(contents, str) else str(contents)

        async with self._rail:
            eval_response = await self._rail.eval(
                content=content,
                mode=effective_mode,
                context=context_str[:2000],  # truncate to avoid oversized context
                domain=self._domain,
                include_issues=True,
                include_suggestions=True,
            )

            result: EvalResult = await self._policy.enforce(
                content=content,
                eval_response=eval_response,
                async_client=self._rail,
            )

        return RAILGeminiResponse(
            content=result.content,
            rail_score=result.score,
            rail_confidence=result.confidence,
            rail_dimensions=result.dimension_scores,
            rail_issues=result.issues,
            threshold_met=result.threshold_met,
            was_regenerated=result.was_regenerated,
            original_content=result.original_content,
            gemini_response=gemini_response,
            model=model,
            usage=usage,
        )
