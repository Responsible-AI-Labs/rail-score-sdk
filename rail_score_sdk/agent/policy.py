"""
Agent policy engine — enforces thresholds and callbacks on tool-call results.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .exceptions import AgentBlockedError
from ._client import AgentDecision


class AgentPolicy(str, enum.Enum):
    """Policy mode applied when a tool call fails thresholds."""
    BLOCK = "block"
    SUGGEST_FIX = "suggest_fix"
    LOG_ONLY = "log_only"
    AUTO_FIX = "auto_fix"


@dataclass
class PolicyCheckResult:
    """Result returned by :meth:`AgentPolicyEngine.check`."""
    blocked: bool
    flagged: bool
    allowed: bool
    score: float
    reason: str = ""
    suggested_params: Optional[Dict[str, Any]] = None
    violated_dimensions: List[str] = field(default_factory=list)


class AgentPolicyEngine:
    """
    Agent-specific policy engine for enforcing thresholds on tool-call results.

    Extends the logic of the existing ``PolicyEngine`` to handle agent tool
    calls, with support for per-tool rules, dimension minimums, and
    custom callbacks.

    Args:
        mode: Policy mode — see :class:`AgentPolicy`.
        default_thresholds: Default block/flag/dimension thresholds applied
            to all tool calls.  Example::

                {
                    "block_below": 5.0,
                    "flag_below": 7.0,
                    "dimension_minimums": {"fairness": 6.0, "safety": 6.0},
                }

        per_tool_thresholds: Per-tool threshold overrides.  Example::

                {
                    "credit_scoring_api": {
                        "block_below": 6.0,
                        "flag_below": 7.5,
                        "dimension_minimums": {"fairness": 7.0},
                    }
                }

        on_block: Callback called with the :class:`AgentDecision` when a tool
            call is blocked.  Receives the result before raising.
        on_flag: Callback called with the :class:`AgentDecision` when a tool
            call is flagged.
        on_allow: Callback called with the :class:`AgentDecision` when a tool
            call is allowed.

    Example::

        engine = AgentPolicyEngine(
            mode=AgentPolicy.BLOCK,
            default_thresholds={
                "block_below": 5.0,
                "flag_below": 7.0,
                "dimension_minimums": {"fairness": 6.0},
            },
            on_block=lambda r: slack_alert(r.decision_reason),
        )

        session = AgentSession(client, agent_id="my-agent",
                               policy_engine=engine)
    """

    def __init__(
        self,
        mode: AgentPolicy | str = AgentPolicy.LOG_ONLY,
        default_thresholds: Optional[Dict[str, Any]] = None,
        per_tool_thresholds: Optional[Dict[str, Dict[str, Any]]] = None,
        on_block: Optional[Callable[[AgentDecision], Any]] = None,
        on_flag: Optional[Callable[[AgentDecision], Any]] = None,
        on_allow: Optional[Callable[[AgentDecision], Any]] = None,
    ) -> None:
        if isinstance(mode, str):
            mode = AgentPolicy(mode)
        self.mode = mode
        self._default = default_thresholds or {}
        self._per_tool = per_tool_thresholds or {}
        self._on_block = on_block
        self._on_flag = on_flag
        self._on_allow = on_allow

    def _get_thresholds(self, tool_name: str) -> Dict[str, Any]:
        merged = dict(self._default)
        merged.update(self._per_tool.get(tool_name, {}))
        return merged

    def _evaluate(self, result: AgentDecision) -> PolicyCheckResult:
        thresholds = self._get_thresholds(result.decision_reason)
        tool_name = ""
        # The tool name isn't directly on AgentDecision, but the engine-level
        # decision already incorporates registry thresholds.  We honour the
        # engine's BLOCK/FLAG signal, then optionally apply additional local
        # thresholds on top.
        engine_decision = result.decision  # "ALLOW" | "FLAG" | "BLOCK"

        score = result.rail_score.score
        block_below: float = thresholds.get("block_below", 0.0)
        flag_below: float = thresholds.get("flag_below", 0.0)
        dim_mins: Dict[str, float] = thresholds.get("dimension_minimums", {})

        # Dimension minimum check
        violated: List[str] = []
        for dim, minimum in dim_mins.items():
            ds = result.dimension_scores.get(dim)
            if ds and ds.score < minimum:
                violated.append(dim)

        local_block = score < block_below or bool(violated)
        local_flag = score < flag_below

        blocked = engine_decision == "BLOCK" or local_block
        flagged = not blocked and (engine_decision == "FLAG" or local_flag)
        allowed = not blocked and not flagged

        reason = result.decision_reason
        if violated:
            reason = f"Dimension minimum violated: {violated}"

        return PolicyCheckResult(
            blocked=blocked,
            flagged=flagged,
            allowed=allowed,
            score=score,
            reason=reason,
            suggested_params=result.suggested_params,
            violated_dimensions=violated or list(result.policy.violated_dimensions),
        )

    def check(self, result: AgentDecision) -> PolicyCheckResult:
        """Apply the configured policy to a tool-call evaluation result.

        Args:
            result: :class:`AgentDecision` from ``client.agent.evaluate_tool_call()``.

        Returns:
            :class:`PolicyCheckResult`.

        Raises:
            AgentBlockedError: If mode is ``BLOCK`` and the result is blocked.
        """
        outcome = self._evaluate(result)

        if outcome.blocked:
            if self._on_block is not None:
                self._on_block(result)
            if self.mode == AgentPolicy.BLOCK:
                raise AgentBlockedError(
                    decision_reason=outcome.reason,
                    rail_score=outcome.score,
                    violated_dimensions=outcome.violated_dimensions,
                    suggested_params=outcome.suggested_params,
                    compliance_violations=result.compliance_violations,
                    event_id=result.event_id,
                )
        elif outcome.flagged:
            if self._on_flag is not None:
                self._on_flag(result)
        else:
            if self._on_allow is not None:
                self._on_allow(result)

        return outcome
