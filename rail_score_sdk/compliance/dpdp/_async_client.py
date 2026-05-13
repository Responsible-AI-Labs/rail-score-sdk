"""Async DPDP compliance client — available as ``client.dpdp``."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from ._client import (
    _DPDP_BASE,
    _parse_audit_result,
    _parse_decision,
    _parse_emit_result,
    _parse_evidence,
    _parse_require_result,
    _parse_scan_result,
    _parse_session,
    _parse_timer_list,
)
from .models import (
    DPDPAuditResult,
    DPDPDecision,
    DPDPEmitResult,
    DPDPEvidenceArtefact,
    DPDPRequireResult,
    DPDPScanResult,
    DPDPSession,
    DPDPTimerList,
)


class AsyncDPDPClient:
    """Async DPDP compliance client — attached as ``client.dpdp``."""

    def __init__(self, client: Any) -> None:
        self._c = client

    async def scan(
        self,
        content: str,
        *,
        pii_action: str = "detect",
        child_detection: bool = True,
        purpose: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> DPDPScanResult:
        """Scan text for Indian PII, child signals, and purpose drift."""
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

        data = await self._c._request("POST", f"{_DPDP_BASE}/scan", json=payload)
        return _parse_scan_result(data)

    async def evaluate(
        self,
        action: str,
        context: Dict[str, Any],
        *,
        session_id: Optional[str] = None,
    ) -> DPDPDecision:
        """Synchronous allow/block/require_action gate."""
        payload: Dict[str, Any] = {
            "action": action,
            "context": context,
        }
        if session_id:
            payload["session_id"] = session_id

        data = await self._c._request("POST", f"{_DPDP_BASE}/evaluate", json=payload)
        return _parse_decision(data)

    async def emit(
        self,
        events: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        session_id: Optional[str] = None,
    ) -> DPDPEmitResult:
        """Record behavioral events for compliance evidence."""
        if isinstance(events, dict):
            events = [events]

        payload: Dict[str, Any] = {"events": events}
        if session_id:
            payload["session_id"] = session_id

        data = await self._c._request("POST", f"{_DPDP_BASE}/emit", json=payload)
        return _parse_emit_result(data)

    async def require(
        self,
        session_id: str,
        workflow_step: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> DPDPRequireResult:
        """Get required actions for the current workflow state."""
        payload: Dict[str, Any] = {
            "session_id": session_id,
            "workflow_step": workflow_step,
        }
        if context:
            payload["context"] = context

        data = await self._c._request("POST", f"{_DPDP_BASE}/require", json=payload)
        return _parse_require_result(data)

    async def evidence(
        self,
        evidence_type: str,
        params: Dict[str, Any],
    ) -> DPDPEvidenceArtefact:
        """Generate audit-grade evidence packets (Pro+ tier)."""
        payload: Dict[str, Any] = {
            "type": evidence_type,
            "params": params,
        }

        data = await self._c._request("POST", f"{_DPDP_BASE}/evidence", json=payload)
        return _parse_evidence(data)

    async def create_session(
        self,
        *,
        entity_type: str = "data_fiduciary",
        purpose: str = "",
        sector: str = "other",
        processes_children: bool = False,
        ttl_hours: int = 24,
    ) -> DPDPSession:
        """Create a new compliance session."""
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

        data = await self._c._request("POST", f"{_DPDP_BASE}/session", json=payload)
        return _parse_session(data)

    async def get_session(self, session_id: str) -> DPDPSession:
        """Retrieve an existing compliance session."""
        payload: Dict[str, Any] = {
            "action": "get",
            "session_id": session_id,
        }

        data = await self._c._request("POST", f"{_DPDP_BASE}/session", json=payload)
        return _parse_session(data)

    async def list_timers(
        self,
        *,
        status: Optional[str] = None,
        timer_type: Optional[str] = None,
        approaching_days: Optional[int] = None,
    ) -> DPDPTimerList:
        """List active compliance timers."""
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if timer_type:
            params["type"] = timer_type
        if approaching_days is not None:
            params["approaching_days"] = approaching_days

        data = await self._c._request("GET", f"{_DPDP_BASE}/timers", params=params)
        return _parse_timer_list(data)

    async def dpdp_audit(
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
        """Run a DPDP system audit with tiered requirement scoring."""
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

        data = await self._c._request("POST", "/railscore/v1/compliance/check", json=payload)
        return _parse_audit_result(data)
