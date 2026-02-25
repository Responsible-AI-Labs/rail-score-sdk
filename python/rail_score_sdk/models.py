"""Data models for RAIL Score SDK v2."""

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

    ``explanation`` and ``issues`` are only populated when requested
    via ``include_explanations`` / ``include_issues``.
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
# Protected content models (/railscore/v1/protected)
# ---------------------------------------------------------------------------


@dataclass
class ProtectedEvalResult:
    """Result from protected endpoint with ``action='evaluate'``."""

    rail_score: RailScore
    threshold_met: bool
    improvement_needed: bool
    improvement_prompt: Optional[str] = None
    dimension_scores: Optional[Dict[str, DimensionScore]] = None


@dataclass
class RegenerateMetadata:
    """Metadata for a regeneration response."""

    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: Optional[int] = None


@dataclass
class ProtectedRegenerateResult:
    """Result from protected endpoint with ``action='regenerate'``."""

    improved_content: str
    issues_addressed: List[str]
    metadata: Optional[RegenerateMetadata] = None


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
# Explanation models (/railscore/v1/explain)
# ---------------------------------------------------------------------------


@dataclass
class ExplainResult:
    """Result from the ``/railscore/v1/explain`` endpoint."""

    explanations: Dict[str, str]


# ---------------------------------------------------------------------------
# Utility models
# ---------------------------------------------------------------------------


@dataclass
class HealthResponse:
    """Response from ``/health``."""

    status: str
    service: str


@dataclass
class VersionResponse:
    """Response from ``/version``."""

    version: str
    api_version: str
    optimizations: Dict[str, bool]
    models_available: List[str]


@dataclass
class ModelInfoResponse:
    """Response from ``/railscore/v1/model/info``."""

    endpoints: Dict[str, Any]
    modes: Dict[str, Any]
    native_model: Dict[str, Any]
    explanation_generator: Dict[str, Any]
