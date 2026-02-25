"""
Drop-in replacement for the OpenAI Python SDK client that auto-evaluates
every chat completion via RAIL Score.

Supports the current ``openai>=1.0`` SDK pattern
(``client.chat.completions.create(...)``).

Usage:
    from rail_score_sdk.integrations import RAILOpenAI

    client = RAILOpenAI(
        openai_api_key="sk-...",
        rail_api_key="rail_xxx",
        rail_threshold=7.0,
        rail_policy="regenerate",
    )

    response = await client.chat_completion(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Explain quantum computing"}],
    )
    print(response.rail_score)
    print(response.content)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from rail_score_sdk.async_client import AsyncRAILClient
from rail_score_sdk.policies import EvalResult, Policy, PolicyEngine


@dataclass
class RAILChatResponse:
    """Enriched response object returned by ``RAILOpenAI``."""

    content: str
    rail_score: float
    rail_confidence: float
    rail_dimensions: Dict[str, Any]
    rail_issues: List[Dict[str, Any]]
    rail_suggestions: List[str]
    threshold_met: bool
    was_regenerated: bool
    original_content: Optional[str]
    # Pass-through from OpenAI
    openai_response: Any = None
    model: str = ""
    usage: Dict[str, int] = field(default_factory=dict)


class RAILOpenAI:
    """
    Wraps the ``openai`` AsyncOpenAI client with automatic RAIL evaluation.

    Parameters
    ----------
    openai_api_key : str
        OpenAI API key.
    rail_api_key : str
        RAIL Score API key.
    rail_threshold : float
        Minimum acceptable RAIL score.
    rail_policy : str or Policy
        ``"log_only"`` | ``"block"`` | ``"regenerate"``.
    rail_mode : str
        ``"basic"`` or ``"deep"``.
    rail_domain : str
        Content domain.
    rail_base_url : str
        Override the RAIL API base URL.
    openai_base_url : str, optional
        Override the OpenAI base URL (for proxies / Azure).
    **openai_kwargs
        Extra keyword arguments forwarded to ``AsyncOpenAI()``.
    """

    def __init__(
        self,
        openai_api_key: str,
        rail_api_key: str,
        *,
        rail_threshold: float = 7.0,
        rail_policy: str | Policy = Policy.LOG_ONLY,
        rail_mode: str = "basic",
        rail_domain: str = "general",
        rail_base_url: str = "https://api.responsibleailabs.ai",
        openai_base_url: Optional[str] = None,
        **openai_kwargs: Any,
    ) -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ImportError(
                "The `openai` package is required for RAILOpenAI. "
                "Install it with: pip install openai"
            ) from exc

        oai_kwargs: Dict[str, Any] = {"api_key": openai_api_key, **openai_kwargs}
        if openai_base_url:
            oai_kwargs["base_url"] = openai_base_url

        self._openai = AsyncOpenAI(**oai_kwargs)
        self._rail = AsyncRAILClient(api_key=rail_api_key, base_url=rail_base_url)
        self._policy = PolicyEngine(policy=rail_policy, threshold=rail_threshold)
        self._mode = rail_mode
        self._domain = rail_domain
        self._threshold = rail_threshold

    async def chat_completion(
        self,
        *,
        model: str,
        messages: List[Dict[str, str]],
        rail_mode: Optional[str] = None,
        rail_skip: bool = False,
        **openai_kwargs: Any,
    ) -> RAILChatResponse:
        """
        Create a chat completion and automatically RAIL-evaluate it.

        Parameters
        ----------
        model : str
            OpenAI model name (e.g. ``"gpt-4o"``).
        messages : list
            Conversation messages.
        rail_mode : str, optional
            Override the default RAIL mode for this call.
        rail_skip : bool
            If True, skip RAIL evaluation entirely (passthrough).
        **openai_kwargs
            Extra arguments forwarded to ``chat.completions.create``.

        Returns
        -------
        RAILChatResponse
        """
        # 1) Call OpenAI
        oai_response = await self._openai.chat.completions.create(
            model=model,
            messages=messages,
            **openai_kwargs,
        )
        content = oai_response.choices[0].message.content or ""
        usage = {}
        if oai_response.usage:
            usage = {
                "prompt_tokens": oai_response.usage.prompt_tokens,
                "completion_tokens": oai_response.usage.completion_tokens,
                "total_tokens": oai_response.usage.total_tokens,
            }

        if rail_skip:
            return RAILChatResponse(
                content=content,
                rail_score=0.0,
                rail_confidence=0.0,
                rail_dimensions={},
                rail_issues=[],
                rail_suggestions=[],
                threshold_met=True,
                was_regenerated=False,
                original_content=None,
                openai_response=oai_response,
                model=oai_response.model,
                usage=usage,
            )

        # 2) RAIL evaluation
        effective_mode = rail_mode or self._mode
        context_parts = [
            f"{m.get('role', 'user')}: {m.get('content', '')}"
            for m in messages[-5:]
        ]

        async with self._rail:
            eval_response = await self._rail.eval(
                content=content,
                mode=effective_mode,
                context="\n".join(context_parts),
                domain=self._domain,
                include_issues=True,
                include_suggestions=True,
            )

            # 3) Policy enforcement
            result: EvalResult = await self._policy.enforce(
                content=content,
                eval_response=eval_response,
                async_client=self._rail,
            )

        return RAILChatResponse(
            content=result.content,
            rail_score=result.score,
            rail_confidence=result.confidence,
            rail_dimensions=result.dimension_scores,
            rail_issues=result.issues,
            rail_suggestions=result.improvement_suggestions,
            threshold_met=result.threshold_met,
            was_regenerated=result.was_regenerated,
            original_content=result.original_content,
            openai_response=oai_response,
            model=oai_response.model,
            usage=usage,
        )
