"""Data models for DPDP compliance responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Phase 1: Content scan models
# ---------------------------------------------------------------------------


@dataclass
class DPDPPiiMatch:
    """A single PII match detected in text."""

    type: str
    value: str
    start: int
    end: int
    masked_value: str
    severity: str = "high"
    section: str = "S.8(5)"
    penalty_crore: int = 250


@dataclass
class DPDPChildSignal:
    """A child-related signal detected in text."""

    signal_type: str
    evidence: str
    detected_age: Optional[int] = None
    section: str = "S.9"


@dataclass
class DPDPViolation:
    """A DPDP compliance violation."""

    check: str
    section: str
    reason: str
    action: str
    found: Optional[str] = None
    severity: str = "medium"


@dataclass
class DPDPContentResult:
    """Result of a DPDP content scan (client-side or server-side)."""

    compliant: bool
    violations: List[DPDPViolation] = field(default_factory=list)
    pii_found: List[DPDPPiiMatch] = field(default_factory=list)
    child_signals: List[DPDPChildSignal] = field(default_factory=list)
    session_flags: List[str] = field(default_factory=list)
    masked_content: Optional[str] = None
    original_content: Optional[str] = None


# ---------------------------------------------------------------------------
# Phase 1: Session state (client-side, for RAILSession integration)
# ---------------------------------------------------------------------------


@dataclass
class DPDPLocalSessionState:
    """Client-side session state for tracking DPDP context across turns."""

    child_data_detected: bool = False
    child_age: Optional[int] = None
    child_consent_verified: bool = False
    pii_found_total: int = 0
    violations: List[DPDPViolation] = field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    session_flags: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 2: Server-side scan response
# ---------------------------------------------------------------------------


@dataclass
class DPDPScanPiiItem:
    """PII item from the server-side /scan response."""

    type: str
    original: str
    masked: str
    position: Dict[str, int]
    severity: str = "high"
    section: str = "S.8(5)"
    penalty_crore: int = 250


@dataclass
class DPDPScanChildSignal:
    """Child signal from the server-side /scan response."""

    type: str
    text: str
    inferred_age: Optional[int] = None
    section: str = "S.9"


@dataclass
class DPDPScanResult:
    """Result from the ``/compliance/dpdp/scan`` endpoint."""

    compliant: bool
    pii_found: List[DPDPScanPiiItem] = field(default_factory=list)
    child_signals: List[DPDPScanChildSignal] = field(default_factory=list)
    child_session: bool = False
    child_actions_required: List[str] = field(default_factory=list)
    purpose_drift: bool = False
    purpose_drift_details: Dict[str, Any] = field(default_factory=dict)
    checks_run: List[str] = field(default_factory=list)
    latency_ms: float = 0.0
    credits_consumed: float = 0.0
    content_masked: Optional[str] = None


# ---------------------------------------------------------------------------
# Phase 2: Session models
# ---------------------------------------------------------------------------


@dataclass
class DPDPSessionState:
    """Server-side session state from the ``/session`` endpoint."""

    consent_status: Dict[str, Any] = field(default_factory=dict)
    notice_shown: bool = False
    child_session: bool = False
    events_count: int = 0
    open_timers: List[Dict[str, Any]] = field(default_factory=list)
    fulfilled_obligations: List[str] = field(default_factory=list)
    pending_obligations: List[str] = field(default_factory=list)


@dataclass
class DPDPSession:
    """A compliance session from the ``/session`` endpoint."""

    session_id: str
    created_at: str
    config: Dict[str, Any] = field(default_factory=dict)
    state: Optional[DPDPSessionState] = None
    credits_consumed: float = 0.0


# ---------------------------------------------------------------------------
# Phase 2: Evaluate response models
# ---------------------------------------------------------------------------


@dataclass
class DPDPViolationDetail:
    """A violation detail from the /evaluate response."""

    rule: str
    section: str
    severity: str = "medium"
    penalty_crore: int = 0
    description: str = ""
    remediation: str = ""


@dataclass
class DPDPCondition:
    """A condition attached to an allow verdict."""

    type: str
    reason: str
    action: str = ""


@dataclass
class DPDPRequiredAction:
    """An action required before proceeding."""

    type: str
    reason: str
    section: str = ""
    priority: int = 1
    details: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DPDPDecision:
    """Result from the ``/compliance/dpdp/evaluate`` endpoint."""

    verdict: str
    violations: List[DPDPViolationDetail] = field(default_factory=list)
    conditions: List[DPDPCondition] = field(default_factory=list)
    required_actions: List[DPDPRequiredAction] = field(default_factory=list)
    required_before_proceed: List[DPDPRequiredAction] = field(default_factory=list)
    session_state: Optional[DPDPSessionState] = None
    credits_consumed: float = 0.0


# ---------------------------------------------------------------------------
# Phase 2: Emit models
# ---------------------------------------------------------------------------


@dataclass
class DPDPEventResult:
    """Result for a single emitted event."""

    event_id: str
    type: str
    status: str = "recorded"
    timers_started: List[str] = field(default_factory=list)
    state_changes: List[str] = field(default_factory=list)


@dataclass
class DPDPEmitResult:
    """Result from the ``/compliance/dpdp/emit`` endpoint."""

    accepted: int = 0
    rejected: int = 0
    events: List[DPDPEventResult] = field(default_factory=list)
    credits_consumed: float = 0.0


# ---------------------------------------------------------------------------
# Phase 2: Require models
# ---------------------------------------------------------------------------


@dataclass
class DPDPRequireResult:
    """Result from the ``/compliance/dpdp/require`` endpoint."""

    required_actions: List[DPDPRequiredAction] = field(default_factory=list)
    session_state: Optional[DPDPSessionState] = None
    credits_consumed: float = 0.0


# ---------------------------------------------------------------------------
# Phase 2: Evidence models
# ---------------------------------------------------------------------------


@dataclass
class DPDPEvidenceArtefact:
    """Result from the ``/compliance/dpdp/evidence`` endpoint."""

    evidence_id: str
    type: str
    generated_at: str
    data: Dict[str, Any] = field(default_factory=dict)
    credits_consumed: float = 0.0


# ---------------------------------------------------------------------------
# Phase 2: Timer models
# ---------------------------------------------------------------------------


@dataclass
class DPDPTimer:
    """A single compliance timer."""

    timer_id: str
    type: str
    started_at: str
    deadline: str
    status: str = "active"
    days_remaining: Optional[int] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    breach_id: Optional[str] = None
    alert_at: Optional[str] = None


@dataclass
class DPDPTimerSummary:
    """Summary of active compliance timers."""

    total_active: int = 0
    overdue: int = 0
    approaching_15_days: int = 0


@dataclass
class DPDPTimerList:
    """Result from the ``/compliance/dpdp/timers`` endpoint."""

    timers: List[DPDPTimer] = field(default_factory=list)
    summary: Optional[DPDPTimerSummary] = None
    credits_consumed: float = 0.0


# ---------------------------------------------------------------------------
# Phase 4: System audit models
# ---------------------------------------------------------------------------


@dataclass
class DPDPTieredRequirement:
    """A DPDP requirement with tier classification and penalty context."""

    requirement_id: str
    requirement: str
    article: str
    reference_url: str
    status: str
    score: float
    confidence: float
    threshold: float
    tier: str = ""
    penalty_ceiling_crore: Optional[int] = None
    enforcement_phase: Optional[str] = None
    chatbot_explanation: Optional[str] = None
    checklist: Optional[List[str]] = None
    issue: Optional[str] = None


@dataclass
class DPDPAuditResult:
    """Enhanced compliance result with DPDP-specific tiered scoring."""

    framework: str
    framework_version: str
    framework_url: str
    evaluated_at: str
    compliance_score: Dict[str, Any] = field(default_factory=dict)
    dimension_scores: Dict[str, Any] = field(default_factory=dict)
    requirements_checked: int = 0
    requirements_passed: int = 0
    requirements_failed: int = 0
    requirements_warned: int = 0
    requirements: List[DPDPTieredRequirement] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    tier_1_score: Optional[float] = None
    tier_2_score: Optional[float] = None
    tier_3_score: Optional[float] = None
    total_penalty_exposure_crore: float = 0.0
    entity_context: Dict[str, Any] = field(default_factory=dict)
    enforcement_timeline: Dict[str, str] = field(default_factory=dict)
    partial_result: bool = False
    from_cache: bool = False
    credits: Optional[float] = None
