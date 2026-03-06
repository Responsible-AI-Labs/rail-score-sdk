"""
Drop-in wrapper for the ``anthropic`` Python SDK that auto-evaluates
every message response via RAIL Score.

Uses the current ``anthropic>=0.30`` SDK pattern
(``client.messages.create(...)``).

Usage:
    from rail_score_sdk.integrations import RAILAnthropic

    client = RAILAnthropic(
        anthropic_api_key="sk-ant-...",
        rail_api_key="rail_xxx",
        rail_threshold=7.0,
    )

    response = await client.message(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Explain quantum computing"}],
    )
    print(response.content)
    print(response.rail_score)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from rail_score_sdk.async_client import AsyncRAILClient
from rail_score_sdk.policies import EvalResult, Policy, PolicyEngine


@dataclass
class RAILAnthropicResponse:
    """Enriched response returned by ``RAILAnthropic``."""

    content: str
    rail_score: float
    rail_confidence: float
    rail_dimensions: Dict[str, Any]
    rail_issues: List[Dict[str, Any]]
    threshold_met: bool
    was_regenerated: bool
    original_content: Optional[str]
    anthropic_response: Any = None
    model: str = ""
    usage: Dict[str, int] = field(default_factory=dict)


class RAILAnthropic:
    """
    Wraps the ``anthropic`` AsyncAnthropic client with RAIL evaluation.

    Parameters
    ----------
    anthropic_api_key : str
        Anthropic API key.
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
        anthropic_api_key: str,
        rail_api_key: str,
        *,
        rail_threshold: float = 7.0,
        rail_policy: str | Policy = Policy.LOG_ONLY,
        rail_mode: str = "basic",
        rail_domain: str = "general",
        rail_base_url: str = "https://api.responsibleailabs.ai",
    ) -> None:
        try:
            from anthropic import AsyncAnthropic
        except ImportError as exc:
            raise ImportError(
                "The `anthropic` package is required. "
                "Install: pip install anthropic"
            ) from exc

        self._anthropic = AsyncAnthropic(api_key=anthropic_api_key)
        self._rail = AsyncRAILClient(api_key=rail_api_key, base_url=rail_base_url)
        self._policy = PolicyEngine(policy=rail_policy, threshold=rail_threshold)
        self._mode = rail_mode
        self._domain = rail_domain

    async def message(
        self,
        *,
        model: str,
        max_tokens: int = 1024,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        rail_mode: Optional[str] = None,
        rail_skip: bool = False,
        **anthropic_kwargs: Any,
    ) -> RAILAnthropicResponse:
        """
        Create a message and auto-evaluate via RAIL.

        Parameters
        ----------
        model : str
            Anthropic model (e.g. ``"claude-sonnet-4-5-20250929"``).
        max_tokens : int
            Maximum tokens to generate.
        messages : list
            Conversation messages.
        system : str, optional
            System prompt.
        rail_mode : str, optional
            Override RAIL mode for this call.
        rail_skip : bool
            Skip RAIL evaluation.
        **anthropic_kwargs
            Extra args forwarded to ``messages.create``.
        """
        create_kwargs: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            **anthropic_kwargs,
        }
        if system:
            create_kwargs["system"] = system

        # 1) Call Anthropic
        ant_response = await self._anthropic.messages.create(**create_kwargs)

        # Extract text from content blocks
        content = ""
        for block in ant_response.content:
            if hasattr(block, "text"):
                content += block.text

        usage = {}
        if ant_response.usage:
            usage = {
                "input_tokens": ant_response.usage.input_tokens,
                "output_tokens": ant_response.usage.output_tokens,
            }

        if rail_skip:
            return RAILAnthropicResponse(
                content=content,
                rail_score=0.0,
                rail_confidence=0.0,
                rail_dimensions={},
                rail_issues=[],
                threshold_met=True,
                was_regenerated=False,
                original_content=None,
                anthropic_response=ant_response,
                model=ant_response.model,
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

            result: EvalResult = await self._policy.enforce(
                content=content,
                eval_response=eval_response,
                async_client=self._rail,
            )

        return RAILAnthropicResponse(
            content=result.content,
            rail_score=result.score,
            rail_confidence=result.confidence,
            rail_dimensions=result.dimension_scores,
            rail_issues=result.issues,
            threshold_met=result.threshold_met,
            was_regenerated=result.was_regenerated,
            original_content=result.original_content,
            anthropic_response=ant_response,
            model=ant_response.model,
            usage=usage,
        )
