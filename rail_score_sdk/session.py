"""
Conversation-aware multi-turn evaluation session.

Tracks the full message history, accumulates per-turn RAIL scores,
and applies the configured policy after each assistant turn.

Usage:
    from rail_score_sdk import RAILSession

    async with RAILSession(api_key="rail_xxx", threshold=7.0, policy="regenerate") as session:
        result = await session.evaluate_turn(
            user_message="What medication should I take?",
            assistant_response="Take 500mg ibuprofen every 4 hours.",
        )
        print(result.score, result.content)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from rail_score_sdk.async_client import AsyncRAILClient
from rail_score_sdk.policies import EvalResult, Policy, PolicyEngine


@dataclass
class TurnRecord:
    """Immutable record of a single conversation turn."""

    turn_number: int
    user_message: str
    assistant_response: str
    eval_result: EvalResult
    timestamp: float = field(default_factory=time.time)


class RAILSession:
    """
    Stateful evaluation session for multi-turn LLM conversations.

    Parameters
    ----------
    api_key : str
        RAIL Score API key.
    threshold : float
        Minimum acceptable RAIL score (0.0-10.0).
    policy : str or Policy
        ``"log_only"`` | ``"block"`` | ``"regenerate"`` | ``"custom"``.
    mode : str
        ``"basic"`` (fast) or ``"deep"`` (detailed with explanations).
    domain : str
        Content domain passed to the API (e.g. ``"healthcare"``).
    usecase : str
        Use-case category (e.g. ``"chatbot"``).
    deep_every_n : int
        Run deep mode every *n* turns even when ``mode="basic"``
        (adaptive quality gating). Set to ``0`` to disable.
    context_window : int
        Number of recent turns to include as context when evaluating.
    base_url : str
        Override the RAIL API base URL.
    custom_callback
        Async callback for Policy.CUSTOM.
    """

    def __init__(
        self,
        api_key: str,
        *,
        threshold: float = 7.0,
        policy: Policy | str = Policy.LOG_ONLY,
        mode: str = "basic",
        domain: str = "general",
        usecase: str = "general",
        deep_every_n: int = 0,
        context_window: int = 5,
        base_url: str = "https://api.responsibleailabs.ai",
        custom_callback: Any = None,
        dimensions: Optional[List[str]] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self.api_key = api_key
        self.threshold = threshold
        self.mode = mode
        self.domain = domain
        self.usecase = usecase
        self.deep_every_n = deep_every_n
        self.context_window = context_window
        self.dimensions = dimensions
        self.weights = weights

        self._client = AsyncRAILClient(api_key=api_key, base_url=base_url)
        self._policy = PolicyEngine(
            policy=policy,
            threshold=threshold,
            custom_callback=custom_callback,
        )

        self._history: List[TurnRecord] = []
        self._turn_counter: int = 0

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------
    async def __aenter__(self) -> "RAILSession":
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self._client.__aexit__(*exc)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    @property
    def history(self) -> List[TurnRecord]:
        """All turn records so far (read-only copy)."""
        return list(self._history)

    @property
    def average_score(self) -> float:
        """Running average RAIL score across all turns."""
        if not self._history:
            return 0.0
        return sum(t.eval_result.score for t in self._history) / len(self._history)

    @property
    def lowest_score(self) -> float:
        """Lowest RAIL score in the session."""
        if not self._history:
            return 0.0
        return min(t.eval_result.score for t in self._history)

    def scores_summary(self) -> Dict[str, Any]:
        """Return a summary dict of session-level metrics."""
        return {
            "total_turns": len(self._history),
            "average_score": round(self.average_score, 2),
            "lowest_score": round(self.lowest_score, 2),
            "turns_below_threshold": sum(
                1 for t in self._history if not t.eval_result.threshold_met
            ),
            "regenerations": sum(
                1 for t in self._history if t.eval_result.was_regenerated
            ),
        }

    # ------------------------------------------------------------------
    # Core evaluation
    # ------------------------------------------------------------------
    def _build_context(self, user_message: str) -> str:
        """
        Build a context string from recent turns so the API
        understands the conversational trajectory.
        """
        recent = self._history[-self.context_window :]
        if not recent:
            return f"User query: {user_message}"

        parts: List[str] = []
        for t in recent:
            parts.append(f"[Turn {t.turn_number}] User: {t.user_message}")
            parts.append(f"[Turn {t.turn_number}] Assistant: {t.assistant_response}")
        parts.append(f"[Current] User: {user_message}")
        return "\n".join(parts)

    def _pick_mode(self) -> str:
        """Decide basic vs deep for this turn."""
        if self.deep_every_n > 0 and self._turn_counter % self.deep_every_n == 0:
            return "deep"
        # Also upgrade to deep if the last turn scored poorly
        if self._history and self._history[-1].eval_result.score < self.threshold - 1.5:
            return "deep"
        return self.mode

    async def evaluate_turn(
        self,
        user_message: str,
        assistant_response: str,
        *,
        mode_override: Optional[str] = None,
        extra_context: str = "",
    ) -> EvalResult:
        """
        Evaluate a single conversation turn.

        1. Scores the ``assistant_response`` via RAIL Score API.
        2. Applies the configured policy (block / regenerate / log).
        3. Records the turn in session history.

        Parameters
        ----------
        user_message : str
            The user's message for this turn.
        assistant_response : str
            The LLM-generated response to evaluate.
        mode_override : str, optional
            Force ``"basic"`` or ``"deep"`` for this turn.
        extra_context : str, optional
            Additional context appended to the evaluation.

        Returns
        -------
        EvalResult
            Contains the (possibly regenerated) content, score, and metadata.
        """
        self._turn_counter += 1
        effective_mode = mode_override or self._pick_mode()
        context = self._build_context(user_message)
        if extra_context:
            context += f"\n{extra_context}"

        # ---- Call RAIL eval API ----
        eval_response = await self._client.eval(
            content=assistant_response,
            mode=effective_mode,
            dimensions=self.dimensions,
            weights=self.weights,
            context=context,
            domain=self.domain,
            usecase=self.usecase,
            include_explanations=(effective_mode == "deep"),
            include_issues=True,
            include_suggestions=True,
        )

        # ---- Apply policy ----
        result = await self._policy.enforce(
            content=assistant_response,
            eval_response=eval_response,
            async_client=self._client,
        )

        # ---- Record turn ----
        record = TurnRecord(
            turn_number=self._turn_counter,
            user_message=user_message,
            assistant_response=result.content,
            eval_result=result,
        )
        self._history.append(record)

        return result

    async def evaluate_input(
        self,
        user_message: str,
        *,
        dimensions: Optional[List[str]] = None,
    ) -> EvalResult:
        """
        Pre-evaluate a user input (e.g. for toxicity, safety).

        Uses basic mode with a reduced dimension set for speed.
        Does NOT record a turn in history.
        """
        dims = dimensions or ["safety", "fairness"]
        eval_response = await self._client.eval(
            content=user_message,
            mode="basic",
            dimensions=dims,
            domain=self.domain,
            usecase=self.usecase,
        )

        rail_score_obj = eval_response.get("rail_score", {})
        return EvalResult(
            content=user_message,
            score=rail_score_obj.get("score", 0.0),
            confidence=rail_score_obj.get("confidence", 0.0),
            threshold_met=rail_score_obj.get("score", 0.0) >= self.threshold,
            dimension_scores=eval_response.get("dimension_scores", {}),
            issues=eval_response.get("issues", []),
            raw_response=eval_response,
        )
