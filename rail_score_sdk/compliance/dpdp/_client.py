"""Sync DPDP compliance client — available as ``client.dpdp``."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from ...exceptions import RailScoreError
from .exceptions import DPDPHostedOnlyError
from .models import (
    DPDPAuditResult,
    DPDPCondition,
    DPDPDecision,
    DPDPEmitResult,
    DPDPEvidenceArtefact,
    DPDPEventResult,
    DPDPRequiredAction,
    DPDPRequireResult,
    DPDPScanChildSignal,
    DPDPScanPiiItem,
    DPDPScanResult,
    DPDPSession,
    DPDPSessionState,
    DPDPTieredRequirement,
    DPDPTimer,
    DPDPTimerList,
    DPDPTimerSummary,
    DPDPViolationDetail,
)

_DPDP_BASE = "/railscore/v1/compliance/dpdp"


# ---------------------------------------------------------------------------
# Shared parsing functions (reused by _async_client.py)
# ---------------------------------------------------------------------------


def _parse_session_state(data: Dict[str, Any]) -> DPDPSessionState:
    return DPDPSessionState(
        consent_status=data.get("consent_status", {}),
        notice_shown=data.get("notice_shown", False),
        child_session=data.get("child_session", False),
        events_count=data.get("events_count", 0),
        open_timers=data.get("open_timers", []),
        fulfilled_obligations=data.get("fulfilled_obligations", []),
        pending_obligations=data.get("pending_obligations", []),
    )


def _parse_violation_detail(data: Dict[str, Any]) -> DPDPViolationDetail:
    return DPDPViolationDetail(
        rule=data.get("rule", ""),
        section=data.get("section", ""),
        severity=data.get("severity", "medium"),
        penalty_crore=data.get("penalty_crore", 0),
        description=data.get("description", ""),
        remediation=data.get("remediation", ""),
    )


def _parse_condition(data: Dict[str, Any]) -> DPDPCondition:
    return DPDPCondition(
        type=data.get("type", ""),
        reason=data.get("reason", ""),
        action=data.get("action", ""),
    )


def _parse_required_action(data: Dict[str, Any]) -> DPDPRequiredAction:
    return DPDPRequiredAction(
        type=data.get("type", ""),
        reason=data.get("reason", ""),
        section=data.get("section", ""),
        priority=data.get("priority", 1),
        details=data.get("details", ""),
        metadata=data.get("metadata", {}),
    )


def _parse_scan_result(data: Dict[str, Any]) -> DPDPScanResult:
    result = data.get("result", data)
    return DPDPScanResult(
        compliant=result.get("compliant", True),
        pii_found=[
            DPDPScanPiiItem(
                type=p.get("type", ""),
                original=p.get("original", ""),
                masked=p.get("masked", ""),
                position=p.get("position", {}),
                severity=p.get("severity", "high"),
                section=p.get("section", "S.8(5)"),
                penalty_crore=p.get("penalty_crore", 250),
            )
            for p in result.get("pii_found", [])
        ],
        child_signals=[
            DPDPScanChildSignal(
                type=cs.get("type", ""),
                text=cs.get("text", ""),
                inferred_age=cs.get("inferred_age"),
                section=cs.get("section", "S.9"),
            )
            for cs in result.get("child_signals", [])
        ],
        child_session=result.get("child_session", False),
        child_actions_required=result.get("child_actions_required", []),
        purpose_drift=result.get("purpose_drift", False),
        purpose_drift_details=result.get("purpose_drift_details", {}),
        checks_run=result.get("checks_run", []),
        latency_ms=result.get("latency_ms", 0.0),
        credits_consumed=data.get("credits_consumed", 0.0),
        content_masked=result.get("content_masked"),
    )


def _parse_decision(data: Dict[str, Any]) -> DPDPDecision:
    result = data.get("result", data)
    state_data = result.get("session_state")
    return DPDPDecision(
        verdict=result.get("verdict", ""),
        violations=[_parse_violation_detail(v) for v in result.get("violations", [])],
        conditions=[_parse_condition(c) for c in result.get("conditions", [])],
        required_actions=[
            _parse_required_action(a) for a in result.get("required_actions", [])
        ],
        required_before_proceed=[
            _parse_required_action(a) for a in result.get("required_before_proceed", [])
        ],
        session_state=_parse_session_state(state_data) if state_data else None,
        credits_consumed=data.get("credits_consumed", 0.0),
    )


def _parse_emit_result(data: Dict[str, Any]) -> DPDPEmitResult:
    result = data.get("result", data)
    return DPDPEmitResult(
        accepted=result.get("accepted", 0),
        rejected=result.get("rejected", 0),
        events=[
            DPDPEventResult(
                event_id=e.get("event_id", ""),
                type=e.get("type", ""),
                status=e.get("status", "recorded"),
                timers_started=e.get("timers_started", []),
                state_changes=e.get("state_changes", []),
            )
            for e in result.get("events", [])
        ],
        credits_consumed=data.get("credits_consumed", 0.0),
    )


def _parse_require_result(data: Dict[str, Any]) -> DPDPRequireResult:
    result = data.get("result", data)
    state_data = result.get("session_state")
    return DPDPRequireResult(
        required_actions=[
            _parse_required_action(a) for a in result.get("required_actions", [])
        ],
        session_state=_parse_session_state(state_data) if state_data else None,
        credits_consumed=data.get("credits_consumed", 0.0),
    )


def _parse_evidence(data: Dict[str, Any]) -> DPDPEvidenceArtefact:
    result = data.get("result", data)
    return DPDPEvidenceArtefact(
        evidence_id=result.get("evidence_id", ""),
        type=result.get("type", ""),
        generated_at=result.get("generated_at", ""),
        data={
            k: v
            for k, v in result.items()
            if k not in ("evidence_id", "type", "generated_at")
        },
        credits_consumed=data.get("credits_consumed", 0.0),
    )


def _parse_session(data: Dict[str, Any]) -> DPDPSession:
    result = data.get("result", data)
    state_data = result.get("state")
    return DPDPSession(
        session_id=result.get("session_id", ""),
        created_at=result.get("created_at", ""),
        config=result.get("config", {}),
        state=_parse_session_state(state_data) if state_data else None,
        credits_consumed=data.get("credits_consumed", 0.0),
    )


def _parse_timer(data: Dict[str, Any]) -> DPDPTimer:
    return DPDPTimer(
        timer_id=data.get("timer_id", ""),
        type=data.get("type", ""),
        started_at=data.get("started_at", ""),
        deadline=data.get("deadline", ""),
        status=data.get("status", "active"),
        days_remaining=data.get("days_remaining"),
        request_id=data.get("request_id"),
        user_id=data.get("user_id"),
        org_id=data.get("org_id"),
        breach_id=data.get("breach_id"),
        alert_at=data.get("alert_at"),
    )


def _parse_timer_list(data: Dict[str, Any]) -> DPDPTimerList:
    result = data.get("result", data)
    summary_data = result.get("summary")
    return DPDPTimerList(
        timers=[_parse_timer(t) for t in result.get("timers", [])],
        summary=(
            DPDPTimerSummary(
                total_active=summary_data.get("total_active", 0),
                overdue=summary_data.get("overdue", 0),
                approaching_days=summary_data.get(
                    "approaching_7_days",
                    summary_data.get("approaching_15_days", 0),
                ),
            )
            if summary_data
            else None
        ),
        credits_consumed=data.get("credits_consumed", 0.0),
    )


def _parse_audit_result(data: Dict[str, Any]) -> DPDPAuditResult:
    result = data.get("result", data)
    return DPDPAuditResult(
        framework=result.get("framework", "india_dpdp"),
        framework_version=result.get("framework_version", ""),
        framework_url=result.get("framework_url", ""),
        evaluated_at=result.get("evaluated_at", ""),
        compliance_score=result.get("compliance_score", {}),
        dimension_scores=result.get("dimension_scores", {}),
        requirements_checked=result.get("requirements_checked", 0),
        requirements_passed=result.get("requirements_passed", 0),
        requirements_failed=result.get("requirements_failed", 0),
        requirements_warned=result.get("requirements_warned", 0),
        requirements=[
            DPDPTieredRequirement(
                requirement_id=r.get("requirement_id", ""),
                requirement=r.get("requirement", ""),
                article=r.get("article", ""),
                reference_url=r.get("reference_url", ""),
                status=r.get("status", ""),
                score=r.get("score", 0.0),
                confidence=r.get("confidence", 0.0),
                threshold=r.get("threshold", 0.0),
                tier=r.get("tier", ""),
                penalty_ceiling_crore=r.get("penalty_ceiling_crore"),
                enforcement_phase=r.get("enforcement_phase"),
                chatbot_explanation=r.get("chatbot_explanation"),
                checklist=r.get("checklist"),
                issue=r.get("issue"),
            )
            for r in result.get("requirements", [])
        ],
        issues=result.get("issues", []),
        improvement_suggestions=result.get("improvement_suggestions", []),
        tier_1_score=result.get("tier_1_score"),
        tier_2_score=result.get("tier_2_score"),
        tier_3_score=result.get("tier_3_score"),
        total_penalty_exposure_crore=result.get("total_penalty_exposure_crore", 0.0),
        entity_context=result.get("entity_context", {}),
        enforcement_timeline=result.get("enforcement_timeline", {}),
        partial_result=result.get("partial_result", False),
        from_cache=result.get("from_cache", False),
        credits=result.get("_credits"),
    )


# ---------------------------------------------------------------------------
# Sync client class
# ---------------------------------------------------------------------------


class DPDPClient:
    """Sync DPDP compliance client — attached as ``client.dpdp``."""

    def __init__(self, client: Any) -> None:
        self._c = client

    def scan(
        self,
        content: str,
        *,
        pii_action: str = "detect",
        child_detection: bool = True,
        purpose: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> DPDPScanResult:
        """Scan text for Indian PII, child signals, and purpose drift.

        Calls ``POST /railscore/v1/compliance/dpdp/scan``.
        """
        payload: Dict[str, Any] = {
            "content": content,
            "config": {
                "pii_action": pii_action,
                "child_detection": child_detection,
            },
        }
        if purpose:
            payload["config"]["purpose"] = purpose
        if session_id:
            payload["config"]["session_id"] = session_id

        data = self._c._request("POST", f"{_DPDP_BASE}/scan", json=payload)
        return _parse_scan_result(data)

    def evaluate(
        self,
        action: str,
        context: Dict[str, Any],
        *,
        session_id: Optional[str] = None,
    ) -> DPDPDecision:
        """Synchronous allow/block/require_action gate.

        Calls ``POST /railscore/v1/compliance/dpdp/evaluate``.
        """
        payload: Dict[str, Any] = {
            "action": action,
            "context": context,
        }
        if session_id:
            payload["session_id"] = session_id

        data = self._c._request("POST", f"{_DPDP_BASE}/evaluate", json=payload)
        return _parse_decision(data)

    def emit(
        self,
        events: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        session_id: Optional[str] = None,
    ) -> DPDPEmitResult:
        """Record behavioral events for compliance evidence.

        Calls ``POST /railscore/v1/compliance/dpdp/emit``.

        Parameters
        ----------
        events : dict or list[dict]
            A single event ``{"type": "...", "data": {...}}`` or a list
            of up to 50 events.
        session_id : str, optional
            Links events to a compliance session.
        """
        if isinstance(events, dict):
            events = [events]

        payload: Dict[str, Any] = {"events": events}
        if session_id:
            payload["session_id"] = session_id

        data = self._c._request("POST", f"{_DPDP_BASE}/emit", json=payload)
        return _parse_emit_result(data)

    def require(
        self,
        session_id: str,
        workflow_step: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> DPDPRequireResult:
        """Get required actions for the current workflow state.

        Calls ``POST /railscore/v1/compliance/dpdp/require``.
        """
        payload: Dict[str, Any] = {
            "session_id": session_id,
            "workflow_step": workflow_step,
        }
        if context:
            payload["context"] = context

        data = self._c._request("POST", f"{_DPDP_BASE}/require", json=payload)
        return _parse_require_result(data)

    def evidence(
        self,
        evidence_type: str,
        params: Dict[str, Any],
    ) -> DPDPEvidenceArtefact:
        """Generate audit-grade evidence packets (Pro+ tier).

        Calls ``POST /railscore/v1/compliance/dpdp/evidence``.
        """
        payload: Dict[str, Any] = {
            "type": evidence_type,
            "params": params,
        }

        data = self._c._request("POST", f"{_DPDP_BASE}/evidence", json=payload)
        return _parse_evidence(data)

    def create_session(
        self,
        *,
        entity_type: str = "data_fiduciary",
        purpose: str = "",
        sector: str = "other",
        processes_children: bool = False,
        ttl_hours: int = 24,
    ) -> DPDPSession:
        """Create a new compliance session.

        Calls ``POST /railscore/v1/compliance/dpdp/session``.
        Raises ValueError if purpose is empty.
        """
        if not purpose or not purpose.strip():
            raise ValueError(
                "purpose is required: the RAIL Score API rejects compliance "
                "sessions without a declared processing purpose (DPDP S.4). "
                "Pass purpose='...' describing why the data is processed."
            )
        payload: Dict[str, Any] = {
            "action": "create",
            "config": {
                "entity_type": entity_type,
                "purpose": purpose,
                "sector": sector,
                "processes_children": processes_children,
                "ttl_hours": ttl_hours,
            },
        }

        data = self._c._request("POST", f"{_DPDP_BASE}/session", json=payload)
        return _parse_session(data)

    def get_session(self, session_id: str) -> DPDPSession:
        """Retrieve an existing compliance session.

        Calls ``POST /railscore/v1/compliance/dpdp/session``.
        """
        payload: Dict[str, Any] = {
            "action": "get",
            "session_id": session_id,
        }

        data = self._c._request("POST", f"{_DPDP_BASE}/session", json=payload)
        return _parse_session(data)

    def list_timers(
        self,
        *,
        status: Optional[str] = None,
        timer_type: Optional[str] = None,
        approaching_days: Optional[int] = None,
    ) -> DPDPTimerList:
        """List active compliance timers.

        Calls ``GET /railscore/v1/compliance/dpdp/timers``.
        """
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if timer_type:
            params["type"] = timer_type
        if approaching_days is not None:
            params["approaching_days"] = approaching_days

        data = self._c._request("GET", f"{_DPDP_BASE}/timers", params=params)
        return _parse_timer_list(data)

    def dpdp_audit(
        self,
        content: str,
        *,
        entity_type: str = "data_fiduciary",
        sector: str = "other",
        processes_children: bool = False,
        cross_border_transfers: bool = False,
        strict_mode: bool = False,
        include_explanations: bool = True,
    ) -> DPDPAuditResult:
        """Run a DPDP system audit with tiered requirement scoring.

        Wraps ``compliance_check(framework="india_dpdp")`` with
        entity-specific context and enhanced response parsing.
        Raises DPDPHostedOnlyError if the audit endpoint is unavailable.
        """
        context: Dict[str, Any] = {
            "entity_type": entity_type,
            "sector": sector,
            "processes_children": processes_children,
            "cross_border_transfers": cross_border_transfers,
        }

        payload: Dict[str, Any] = {
            "content": content,
            "framework": "india_dpdp",
            "strict_mode": strict_mode,
            "include_explanations": include_explanations,
            "context": context,
        }

        try:
            data = self._c._request(
                "POST", "/railscore/v1/compliance/check", json=payload
            )
        except RailScoreError as e:
            if getattr(e, "status_code", None) in (404, 501):
                raise DPDPHostedOnlyError(
                    "dpdp_audit is available on the hosted RAIL Score API only. "
                    "Point base_url at https://api.responsibleailabs.ai to run "
                    "audits."
                ) from e
            raise
        return _parse_audit_result(data)
