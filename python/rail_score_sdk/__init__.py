"""
RAIL Score Python SDK

Official Python client library for the RAIL Score API.
Evaluate AI-generated content across 8 dimensions of Responsible AI.

Example:
    >>> from rail_score_sdk import RailScoreClient
    >>> client = RailScoreClient(api_key="rail_xxx...")
    >>> result = client.eval(
    ...     content="AI should be fair and transparent.",
    ...     mode="basic",
    ... )
    >>> print(f"Score: {result.rail_score.score}/10 — {result.rail_score.summary}")
"""

from .client import RailScoreClient
from .models import (
    RailScore,
    DimensionScore,
    Issue,
    EvalResult,
    ProtectedEvalResult,
    ProtectedRegenerateResult,
    RegenerateMetadata,
    ComplianceScore,
    ComplianceDimensionScore,
    RequirementResult,
    ComplianceIssue,
    RiskClassificationDetail,
    ComplianceResult,
    CrossFrameworkSummary,
    MultiComplianceResult,
    HealthResponse,
    VersionResponse,
)
from .exceptions import (
    RailScoreError,
    AuthenticationError,
    InsufficientCreditsError,
    InsufficientTierError,
    ValidationError,
    ContentTooHarmfulError,
    RateLimitError,
    EvaluationFailedError,
    NotImplementedByServerError,
    ServiceUnavailableError,
)

__version__ = "2.0.0"
__all__ = [
    # Client
    "RailScoreClient",
    # Eval models
    "RailScore",
    "DimensionScore",
    "Issue",
    "EvalResult",
    # Protected models
    "ProtectedEvalResult",
    "ProtectedRegenerateResult",
    "RegenerateMetadata",
    # Compliance models
    "ComplianceScore",
    "ComplianceDimensionScore",
    "RequirementResult",
    "ComplianceIssue",
    "RiskClassificationDetail",
    "ComplianceResult",
    "CrossFrameworkSummary",
    "MultiComplianceResult",
    # Utility models
    "HealthResponse",
    "VersionResponse",
    # Exceptions
    "RailScoreError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "InsufficientTierError",
    "ValidationError",
    "ContentTooHarmfulError",
    "RateLimitError",
    "EvaluationFailedError",
    "NotImplementedByServerError",
    "ServiceUnavailableError",
]
