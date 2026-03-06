"""
Policy engine that decides what happens when an LLM response
crosses (or doesn't cross) the RAIL score threshold.

Policies:
    - log_only   -> always pass through, just attach scores
    - block      -> raise RAILBlockedError if score < threshold
    - regenerate -> call /safe-regenerate for improved content
    - custom     -> call user-supplied async callback

Usage:
    from rail_score_sdk.policies import PolicyEngine, Policy

    engine = PolicyEngine(
        policy=Policy.REGENERATE,
        threshold=7.0,
    )
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, List, Optional


class Policy(str, enum.Enum):
    LOG_ONLY = "log_only"
    BLOCK = "block"
    REGENERATE = "regenerate"
    CUSTOM = "custom"


class RAILBlockedError(Exception):
    """Raised when the ``block`` policy triggers."""

    def __init__(
        self,
        score: float,
        threshold: float,
        issues: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.score = score
        self.threshold = threshold
        self.issues = issues or []
        super().__init__(
            f"RAIL score {score:.1f} is below threshold {threshold:.1f}. "
            f"Content blocked by policy."
        )


@dataclass
class EvalResult:
    """Return value for every policy enforcement."""

    content: str
    score: float
    confidence: float
    threshold_met: bool
    dimension_scores: Dict[str, Any] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    was_regenerated: bool = False
    original_content: Optional[str] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)


# Type alias for a custom policy callback.
# Receives (content, eval_result_dict, async_client) -> new content str or None.
CustomPolicyCallback = Callable[
    [str, Dict[str, Any], Any],
    Awaitable[Optional[str]],
]


class PolicyEngine:
    """Decides what happens after a RAIL evaluation."""

    def __init__(
        self,
        policy: Policy | str = Policy.LOG_ONLY,
        threshold: float = 7.0,
        custom_callback: Optional[CustomPolicyCallback] = None,
        regenerate_max_retries: int = 1,
    ) -> None:
        if isinstance(policy, str):
            policy = Policy(policy)
        self.policy = policy
        self.threshold = threshold
        self.custom_callback = custom_callback
        self.regenerate_max_retries = regenerate_max_retries

        if policy == Policy.CUSTOM and custom_callback is None:
            raise ValueError(
                "Policy.CUSTOM requires a `custom_callback` async function."
            )

    async def enforce(
        self,
        content: str,
        eval_response: Dict[str, Any],
        async_client: Any,  # AsyncRAILClient — avoids circular import
    ) -> EvalResult:
        """
        Apply the configured policy to an evaluation result.

        Parameters
        ----------
        content : str
            The original LLM-generated text.
        eval_response : dict
            The ``result`` dict returned by ``/railscore/v1/eval``.
        async_client : AsyncRAILClient
            Used if regeneration is needed.

        Returns
        -------
        EvalResult
        """
        rail_score_obj = eval_response.get("rail_score", {})
        score = rail_score_obj.get("score", 0.0)
        confidence = rail_score_obj.get("confidence", 0.0)
        threshold_met = score >= self.threshold
        dimension_scores = eval_response.get("dimension_scores", {})
        issues = eval_response.get("issues", [])
        suggestions = eval_response.get("improvement_suggestions", [])

        result = EvalResult(
            content=content,
            score=score,
            confidence=confidence,
            threshold_met=threshold_met,
            dimension_scores=dimension_scores,
            issues=issues,
            improvement_suggestions=suggestions,
            raw_response=eval_response,
        )

        if threshold_met:
            return result

        # ---- Below-threshold handling ----------------------------------
        if self.policy == Policy.LOG_ONLY:
            return result

        if self.policy == Policy.BLOCK:
            raise RAILBlockedError(
                score=score,
                threshold=self.threshold,
                issues=issues,
            )

        if self.policy == Policy.REGENERATE:
            return await self._regenerate(content, result, async_client)

        if self.policy == Policy.CUSTOM and self.custom_callback is not None:
            new_content = await self.custom_callback(
                content, eval_response, async_client
            )
            if new_content is not None:
                result.original_content = content
                result.content = new_content
                result.was_regenerated = True
            return result

        return result  # fallback

    async def _regenerate(
        self,
        content: str,
        result: EvalResult,
        async_client: Any,
    ) -> EvalResult:
        """Attempt regeneration via the safe-regenerate endpoint."""
        for attempt in range(self.regenerate_max_retries):
            try:
                regen = await async_client.safe_regenerate(
                    content=content,
                    mode="basic",
                    max_regenerations=1,
                    regeneration_model="RAIL_Safe_LLM",
                    thresholds={"overall": {"score": self.threshold}},
                )
                regen_result = regen.get("result", regen)
                improved = regen_result.get("best_content")
                if improved:
                    result.original_content = content
                    result.content = improved
                    result.was_regenerated = True
                    return result
            except Exception:
                if attempt == self.regenerate_max_retries - 1:
                    raise
        return result
