"""Data models for RAIL Score SDK v2.2."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


# ---------------------------------------------------------------------------
# Evaluation models (/railscore/v1/eval)
# ---------------------------------------------------------------------------


@dataclass
class RailScore:
    """Overall RAIL score with confidence and summary."""

    score: float
    confidence: float
    summary: str


@dataclass
class DimensionScore:
    """Per-dimension score returned by the evaluation endpoint.

    ``explanation`` and ``issues`` are only populated in deep mode
    or when requested via ``include_explanations`` / ``include_issues``.
    """

    score: float
    confidence: float
    explanation: Optional[str] = None
    issues: Optional[List[str]] = None


@dataclass
class Issue:
    """An issue identified during evaluation."""

    dimension: str
    description: str


@dataclass
class EvalResult:
    """Result from the ``/railscore/v1/eval`` endpoint."""

    rail_score: RailScore
    explanation: str
    dimension_scores: Dict[str, DimensionScore]
    issues: Optional[List[Issue]] = None
    improvement_suggestions: Optional[List[str]] = None
    from_cache: bool = False


# ---------------------------------------------------------------------------
# Safe-Regenerate models (/railscore/v1/safe-regenerate)
# ---------------------------------------------------------------------------


@dataclass
class ThresholdDimensionResult:
    """Per-dimension threshold evaluation result."""

    score: float
    threshold: float
    confidence: float
    confidence_threshold: float
    passed: bool
    required: bool


@dataclass
class ThresholdsMet:
    """Threshold evaluation summary."""

    overall_passed: bool
    all_passed: bool
    all_required_passed: Optional[bool] = None
    dimension_failures_count: Optional[int] = None
    dimension_results: Optional[Dict[str, ThresholdDimensionResult]] = None


@dataclass
class IterationRecord:
    """Record of a single safe-regenerate iteration."""

    iteration: int
    content: str
    scores: Optional[Dict[str, Any]] = None
    thresholds_met: Optional[bool] = None
    failing_dimensions: Optional[List[str]] = None
    improvement_from_previous: Optional[float] = None
    latency_ms: Optional[float] = None
    rail_prompt: Optional[Any] = None
    regeneration_model: Optional[str] = None


@dataclass
class RailPrompt:
    """Prompt returned in external mode for client-side regeneration."""

    system_prompt: str
    user_prompt: str
    temperature: Optional[float] = None


@dataclass
class SafeRegenerateMetadata:
    """Metadata for a safe-regenerate response."""

    req_id: str
    mode: str
    total_iterations: Optional[int] = None
    total_latency_ms: Optional[float] = None


@dataclass
class CreditsBreakdown:
    """Breakdown of credits consumed during safe-regenerate."""

    evaluations: float
    regenerations: float
    total: float


@dataclass
class SafeRegenerateResult:
    """Result from ``/railscore/v1/safe-regenerate``.

    The shape varies by ``status``:
    - ``"passed"`` / ``"max_iterations_reached"``: contains ``best_content``
      and ``iteration_history``.
    - ``"awaiting_regeneration"`` (external mode): contains ``session_id``
      and ``rail_prompt``.
    """

    status: str
    original_content: str
    credits_consumed: float
    metadata: Optional[SafeRegenerateMetadata] = None
    credits_breakdown: Optional[CreditsBreakdown] = None
    # Present when status is passed / max_iterations_reached
    best_content: Optional[str] = None
    best_iteration: Optional[int] = None
    best_scores: Optional[Dict[str, Any]] = None
    iteration_history: Optional[List[IterationRecord]] = None
    # Present when status is awaiting_regeneration (external mode)
    session_id: Optional[str] = None
    iteration: Optional[int] = None
    iterations_remaining: Optional[int] = None
    current_scores: Optional[Dict[str, Any]] = None
    rail_prompt: Optional[RailPrompt] = None


@dataclass
class CriticalContentEvaluation:
    """Evaluation returned when content is flagged as critically unsafe (422)."""

    rail_score: RailScore
    dimension_scores: Dict[str, DimensionScore]
    failing_dimensions: List[str]


# ---------------------------------------------------------------------------
# Compliance models (/railscore/v1/compliance/check)
# ---------------------------------------------------------------------------


@dataclass
class ComplianceScore:
    """Overall compliance score for a framework."""

    score: float
    confidence: float
    label: str
    summary: str


@dataclass
class ComplianceDimensionScore:
    """Per-dimension score within a compliance evaluation."""

    score: float
    confidence: float
    explanation: Optional[str] = None
    issues: Optional[List[str]] = None


@dataclass
class RequirementResult:
    """Detailed result for a single compliance requirement."""

    requirement_id: str
    requirement: str
    article: str
    reference_url: str
    status: str
    score: float
    confidence: float
    threshold: float
    ai_specific: bool
    dimension_sources: List[str]
    evaluation_method: str
    issue: Optional[str] = None
    regulatory_deadline: Optional[str] = None
    penalty_exposure: Optional[str] = None


@dataclass
class ComplianceIssue:
    """A compliance issue with remediation guidance."""

    id: str
    description: str
    dimension: str
    severity: str
    requirement: str
    article: str
    reference_url: str
    remediation_effort: str
    remediation_deadline_days: Optional[int] = None
    remediation_deadline_date: Optional[str] = None


@dataclass
class RiskClassificationDetail:
    """EU AI Act risk classification detail."""

    tier: str
    basis: str
    obligations: Optional[List[str]] = None


@dataclass
class ComplianceResult:
    """Result from ``/railscore/v1/compliance/check`` for a single framework."""

    framework: str
    framework_version: str
    framework_url: str
    evaluated_at: str
    compliance_score: ComplianceScore
    dimension_scores: Dict[str, ComplianceDimensionScore]
    requirements_checked: int
    requirements_passed: int
    requirements_failed: int
    requirements_warned: int
    requirements: List[RequirementResult]
    issues: List[ComplianceIssue]
    improvement_suggestions: List[str]
    risk_classification_detail: Optional[RiskClassificationDetail] = None
    partial_result: bool = False
    from_cache: bool = False
    credits: Optional[float] = None


@dataclass
class CrossFrameworkSummary:
    """Summary across multiple compliance frameworks."""

    frameworks_evaluated: int
    average_score: float
    weakest_framework: str
    weakest_score: float
    credits: Optional[float] = None


@dataclass
class MultiComplianceResult:
    """Result from multi-framework compliance evaluation."""

    results: Dict[str, ComplianceResult]
    cross_framework_summary: CrossFrameworkSummary


# ---------------------------------------------------------------------------
# Utility models
# ---------------------------------------------------------------------------


@dataclass
class HealthResponse:
    """Response from ``/health``."""

    status: str
    service: str
