"""
India DPDP behavioral compliance for RAIL Score SDK.

Three modes of operation:

- **Mode A (Content Scan):** Real-time PII detection/masking, child signal
  detection, and purpose-drift checking.  Runs inside ``RAILMiddleware``,
  ``RAILSession``, and LLM wrappers.

- **Mode B (Event Stream):** Behavioral, stateful compliance via structured
  events.  Use ``DPDPCompliance`` or ``client.dpdp`` to emit events, evaluate
  gates, query required actions, and generate evidence.

- **Mode C (System Audit):** Enhanced ``compliance_check()`` with tiered DPDP
  requirements, penalty-weighted scoring, and enforcement-timeline context.

Quick start::

    from rail_score_sdk.compliance.dpdp import DPDPCompliance, DPDPConfig

    dpdp = DPDPCompliance(api_key="rail-...", config=DPDPConfig(
        entity_type="data_fiduciary",
        purpose="loan_advisory",
        pii_action="mask",
    ))

    # Server-side scan
    result = await dpdp.scan("Aadhaar: 2345 6789 0123")

    # Evaluate gate
    decision = await dpdp.evaluate("process_data", {"user_id": "u_hash", "purpose": "loan_advisory"})
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from .config import DPDPConfig
from .exceptions import (
    DPDPBlockedError,
    DPDPChildContentBlockedError,
    DPDPConsentRequiredError,
    DPDPError,
    DPDPPiiBlockedError,
    DPDPSessionNotFoundError,
    DPDPTimerExpiredError,
)
from .models import (
    DPDPAuditResult,
    DPDPChildSignal,
    DPDPCondition,
    DPDPContentResult,
    DPDPDecision,
    DPDPEmitResult,
    DPDPEvidenceArtefact,
    DPDPEventResult,
    DPDPLocalSessionState,
    DPDPPiiMatch,
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
    DPDPViolation,
    DPDPViolationDetail,
)
from .scanner import DPDPContentScanner


class DPDPCompliance:
    """Standalone DPDP compliance client.

    Combines server-side API calls (scan, evaluate, emit, require,
    evidence, session, timers) with an optional client-side content
    scanner for zero-latency local PII detection.

    Can be used as an async context manager::

        async with DPDPCompliance(api_key="rail-...", config=config) as dpdp:
            result = await dpdp.scan("text with PII...")
    """

    def __init__(
        self,
        api_key: str,
        config: Optional[DPDPConfig] = None,
        base_url: str = "https://api.responsibleailabs.ai",
    ) -> None:
        from rail_score_sdk.async_client import AsyncRAILClient
        from ._async_client import AsyncDPDPClient

        self._config = config or DPDPConfig()
        self._client = AsyncRAILClient(api_key=api_key, base_url=base_url)
        self._dpdp = AsyncDPDPClient(self._client)
        self._scanner = DPDPContentScanner(self._config)

    async def __aenter__(self) -> DPDPCompliance:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self._client.__aexit__(*exc)

    # ------------------------------------------------------------------
    # Server-side API methods
    # ------------------------------------------------------------------

    async def scan(
        self,
        content: str,
        *,
        pii_action: Optional[str] = None,
        child_detection: bool = True,
        purpose: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> DPDPScanResult:
        """Server-side content scan via ``/compliance/dpdp/scan``."""
        return await self._dpdp.scan(
            content,
            pii_action=pii_action or self._config.pii_action,
            child_detection=child_detection,
            purpose=purpose or self._config.purpose or None,
            session_id=session_id,
        )

    async def evaluate(
        self,
        action: str,
        context: Dict[str, Any],
        *,
        session_id: Optional[str] = None,
    ) -> DPDPDecision:
        """Synchronous allow/block/require_action gate."""
        return await self._dpdp.evaluate(action, context, session_id=session_id)

    async def emit(
        self,
        events: Union[Dict[str, Any], List[Dict[str, Any]]],
        *,
        session_id: Optional[str] = None,
    ) -> DPDPEmitResult:
        """Record behavioral events."""
        return await self._dpdp.emit(events, session_id=session_id)

    async def require(
        self,
        session_id: str,
        workflow_step: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> DPDPRequireResult:
        """Get required actions for a workflow step."""
        return await self._dpdp.require(session_id, workflow_step, context)

    async def evidence(
        self,
        evidence_type: str,
        params: Dict[str, Any],
    ) -> DPDPEvidenceArtefact:
        """Generate audit-grade evidence packets."""
        return await self._dpdp.evidence(evidence_type, params)

    async def create_session(self, **kwargs: Any) -> DPDPSession:
        """Create a compliance session."""
        defaults = self._config.to_session_config()
        defaults.update({k: v for k, v in kwargs.items() if v is not None})
        return await self._dpdp.create_session(**defaults)

    async def get_session(self, session_id: str) -> DPDPSession:
        """Retrieve an existing compliance session."""
        return await self._dpdp.get_session(session_id)

    async def list_timers(self, **kwargs: Any) -> DPDPTimerList:
        """List active compliance timers."""
        return await self._dpdp.list_timers(**kwargs)

    async def dpdp_audit(self, content: str, **kwargs: Any) -> DPDPAuditResult:
        """Run a DPDP system audit with tiered requirement scoring."""
        defaults: Dict[str, Any] = {
            "entity_type": self._config.entity_type,
            "sector": self._config.sector,
            "processes_children": self._config.processes_children,
            "cross_border_transfers": self._config.cross_border_transfers,
        }
        defaults.update({k: v for k, v in kwargs.items() if v is not None})
        return await self._dpdp.dpdp_audit(content, **defaults)

    # ------------------------------------------------------------------
    # Client-side scanning (zero latency, no API call)
    # ------------------------------------------------------------------

    def scan_local(
        self,
        text: str,
        session_flags: Optional[List[str]] = None,
    ) -> DPDPContentResult:
        """Client-side regex scan — zero latency, no API call."""
        return self._scanner.scan_text(text, session_flags=session_flags)


__all__ = [
    # Main entry point
    "DPDPCompliance",
    # Configuration
    "DPDPConfig",
    # Scanner
    "DPDPContentScanner",
    # Phase 1 models (content scan)
    "DPDPPiiMatch",
    "DPDPChildSignal",
    "DPDPViolation",
    "DPDPContentResult",
    "DPDPLocalSessionState",
    # Phase 2 models (scan response)
    "DPDPScanPiiItem",
    "DPDPScanChildSignal",
    "DPDPScanResult",
    # Phase 2 models (session)
    "DPDPSession",
    "DPDPSessionState",
    # Phase 2 models (evaluate)
    "DPDPViolationDetail",
    "DPDPCondition",
    "DPDPRequiredAction",
    "DPDPDecision",
    # Phase 2 models (emit)
    "DPDPEventResult",
    "DPDPEmitResult",
    # Phase 2 models (require)
    "DPDPRequireResult",
    # Phase 2 models (evidence)
    "DPDPEvidenceArtefact",
    # Phase 2 models (timers)
    "DPDPTimer",
    "DPDPTimerSummary",
    "DPDPTimerList",
    # Phase 4 models (audit)
    "DPDPTieredRequirement",
    "DPDPAuditResult",
    # Exceptions
    "DPDPError",
    "DPDPBlockedError",
    "DPDPChildContentBlockedError",
    "DPDPPiiBlockedError",
    "DPDPConsentRequiredError",
    "DPDPTimerExpiredError",
    "DPDPSessionNotFoundError",
]
