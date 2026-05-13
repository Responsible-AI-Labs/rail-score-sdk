"""Agent-specific exceptions."""

from typing import Any, Dict, List, Optional


class AgentBlockedError(Exception):
    """Raised when a tool call is blocked by policy."""

    def __init__(
        self,
        decision_reason: str,
        rail_score: float = 0.0,
        violated_dimensions: Optional[List[str]] = None,
        suggested_params: Optional[Dict[str, Any]] = None,
        compliance_violations: Optional[List[Any]] = None,
        event_id: str = "",
    ) -> None:
        self.decision_reason = decision_reason
        self.rail_score = rail_score
        self.violated_dimensions = violated_dimensions or []
        self.suggested_params = suggested_params
        self.compliance_violations = compliance_violations or []
        self.event_id = event_id
        super().__init__(decision_reason)


class PlanBlockedError(Exception):
    """Raised when an entire plan is blocked (BLOCK_ALL)."""

    def __init__(
        self,
        overall_decision: str,
        blocked_steps: Optional[List[int]] = None,
        plan_summary: str = "",
    ) -> None:
        self.overall_decision = overall_decision
        self.blocked_steps = blocked_steps or []
        self.plan_summary = plan_summary
        super().__init__(
            f"Plan blocked: {overall_decision}. " f"Blocked steps: {self.blocked_steps}"
        )


class SessionClosedError(Exception):
    """Raised when an operation is attempted on a closed session."""

    pass


class AgentSessionExpiredError(Exception):
    """Raised when an operation is attempted on an expired session."""

    pass
