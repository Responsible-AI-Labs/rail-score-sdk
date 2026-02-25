"""
Pushes RAIL Score evaluation results into Langfuse v3 as custom scores
attached to traces/observations.

Uses the Langfuse Python SDK v3 (``langfuse>=3.0``) with the
``get_client()`` / ``create_score()`` pattern.

Usage -- standalone:
    from rail_score_sdk.integrations import RAILLangfuse

    rl = RAILLangfuse(
        rail_api_key="rail_xxx",
        langfuse_public_key="pk-lf-...",
        langfuse_secret_key="sk-lf-...",
    )
    await rl.evaluate_and_log(
        content="LLM response here",
        trace_id="trace-abc-123",
    )

Usage -- as a callback attached to RAILSession:
    from rail_score_sdk import RAILSession
    from rail_score_sdk.integrations import RAILLangfuse

    langfuse_cb = RAILLangfuse(rail_api_key="rail_xxx")

    session = RAILSession(api_key="rail_xxx", threshold=7.0)
    result = await session.evaluate_turn(user_message="...", assistant_response="...")
    langfuse_cb.log_eval_result(result, trace_id="trace-abc-123")
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from rail_score_sdk.async_client import AsyncRAILClient
from rail_score_sdk.policies import EvalResult

logger = logging.getLogger("rail_score_sdk.langfuse")

# The 8 RAIL dimensions
RAIL_DIMENSIONS = [
    "fairness",
    "safety",
    "reliability",
    "transparency",
    "privacy",
    "accountability",
    "inclusivity",
    "user_impact",
]


class RAILLangfuse:
    """
    Bridges RAIL Score evaluations with Langfuse v3 scoring.

    Parameters
    ----------
    rail_api_key : str
        RAIL Score API key.
    langfuse_public_key : str, optional
        Langfuse public key. Can also be set via env ``LANGFUSE_PUBLIC_KEY``.
    langfuse_secret_key : str, optional
        Langfuse secret key. Can also be set via env ``LANGFUSE_SECRET_KEY``.
    langfuse_base_url : str, optional
        Langfuse host. Defaults to env ``LANGFUSE_BASE_URL``
        or ``https://cloud.langfuse.com``.
    rail_mode : str
        Default RAIL evaluation mode.
    rail_domain : str
        Default content domain.
    score_dimensions : bool
        If True, push all 8 dimension scores individually in addition
        to the overall score.
    score_prefix : str
        Prefix for score names in Langfuse (e.g. ``"rail_"`` ->
        ``"rail_overall"``, ``"rail_fairness"``, etc.).
    rail_base_url : str
        Override the RAIL API base URL.
    """

    def __init__(
        self,
        rail_api_key: str,
        *,
        langfuse_public_key: Optional[str] = None,
        langfuse_secret_key: Optional[str] = None,
        langfuse_base_url: Optional[str] = None,
        rail_mode: str = "basic",
        rail_domain: str = "general",
        score_dimensions: bool = True,
        score_prefix: str = "rail_",
        rail_base_url: str = "https://api.responsibleailabs.ai",
    ) -> None:
        try:
            from langfuse import get_client as _get_langfuse_client
        except ImportError as exc:
            raise ImportError(
                "The `langfuse` package (v3+) is required. "
                "Install: pip install langfuse>=3.0"
            ) from exc

        # Initialise Langfuse client
        lf_kwargs: Dict[str, Any] = {}
        if langfuse_public_key:
            lf_kwargs["public_key"] = langfuse_public_key
        if langfuse_secret_key:
            lf_kwargs["secret_key"] = langfuse_secret_key
        if langfuse_base_url:
            lf_kwargs["host"] = langfuse_base_url

        # get_client() is the v3 way — it returns the singleton client.
        # If env vars are set it picks them up automatically.
        self._langfuse = _get_langfuse_client(**lf_kwargs) if lf_kwargs else _get_langfuse_client()

        self._rail = AsyncRAILClient(api_key=rail_api_key, base_url=rail_base_url)
        self._mode = rail_mode
        self._domain = rail_domain
        self._score_dimensions = score_dimensions
        self._prefix = score_prefix

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def log_eval_result(
        self,
        result: EvalResult,
        *,
        trace_id: str,
        observation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> None:
        """
        Push a pre-computed EvalResult into Langfuse.

        Creates one ``NUMERIC`` score for the overall RAIL score
        and (optionally) one per dimension.

        Parameters
        ----------
        result : EvalResult
            Output of ``RAILSession.evaluate_turn`` or policy enforcement.
        trace_id : str
            Langfuse trace ID to attach scores to.
        observation_id : str, optional
            Attach to a specific observation within the trace.
        session_id : str, optional
            Attach to a Langfuse session.
        comment : str, optional
            Human-readable comment attached to the overall score.
        """
        # Overall score
        self._push_score(
            name=f"{self._prefix}overall",
            value=result.score,
            trace_id=trace_id,
            observation_id=observation_id,
            session_id=session_id,
            comment=comment or f"RAIL Score: {result.score:.1f}/10",
            metadata={
                "confidence": result.confidence,
                "threshold_met": result.threshold_met,
                "was_regenerated": result.was_regenerated,
            },
        )

        # Per-dimension scores
        if self._score_dimensions and result.dimension_scores:
            for dim_name in RAIL_DIMENSIONS:
                dim_data = result.dimension_scores.get(dim_name)
                if dim_data is None:
                    continue
                dim_score = (
                    dim_data if isinstance(dim_data, (int, float))
                    else dim_data.get("score", 0)
                )
                dim_confidence = (
                    0.0 if isinstance(dim_data, (int, float))
                    else dim_data.get("confidence", 0)
                )
                self._push_score(
                    name=f"{self._prefix}{dim_name}",
                    value=float(dim_score),
                    trace_id=trace_id,
                    observation_id=observation_id,
                    session_id=session_id,
                    metadata={"confidence": dim_confidence},
                )

    async def evaluate_and_log(
        self,
        content: str,
        *,
        trace_id: str,
        observation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        mode: Optional[str] = None,
        domain: Optional[str] = None,
        context: str = "",
    ) -> EvalResult:
        """
        Run a RAIL evaluation and immediately push scores to Langfuse.

        Parameters
        ----------
        content : str
            Text to evaluate.
        trace_id : str
            Langfuse trace ID.
        observation_id, session_id : str, optional
            Optional Langfuse identifiers.
        mode : str, optional
            Override RAIL mode.
        domain : str, optional
            Override content domain.
        context : str
            Extra evaluation context.

        Returns
        -------
        EvalResult
        """
        effective_mode = mode or self._mode
        effective_domain = domain or self._domain

        async with self._rail:
            eval_response = await self._rail.eval(
                content=content,
                mode=effective_mode,
                domain=effective_domain,
                context=context,
                include_issues=True,
                include_suggestions=True,
            )

        # Build an EvalResult from the raw response
        rail_score_obj = eval_response.get("rail_score", {})
        result = EvalResult(
            content=content,
            score=rail_score_obj.get("score", 0.0),
            confidence=rail_score_obj.get("confidence", 0.0),
            threshold_met=True,  # no policy enforcement here
            dimension_scores=eval_response.get("dimension_scores", {}),
            issues=eval_response.get("issues", []),
            improvement_suggestions=eval_response.get("improvement_suggestions", []),
            raw_response=eval_response,
        )

        # Push to Langfuse
        self.log_eval_result(
            result,
            trace_id=trace_id,
            observation_id=observation_id,
            session_id=session_id,
        )

        return result

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _push_score(
        self,
        name: str,
        value: float,
        trace_id: str,
        observation_id: Optional[str] = None,
        session_id: Optional[str] = None,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Push a single numeric score to Langfuse."""
        try:
            kwargs: Dict[str, Any] = {
                "name": name,
                "value": value,
                "trace_id": trace_id,
                "data_type": "NUMERIC",
            }
            if observation_id:
                kwargs["observation_id"] = observation_id
            if session_id:
                kwargs["session_id"] = session_id
            if comment:
                kwargs["comment"] = comment
            if metadata:
                kwargs["metadata"] = metadata

            self._langfuse.create_score(**kwargs)
        except Exception as exc:
            logger.warning("Failed to push score '%s' to Langfuse: %s", name, exc)
