"""
RAIL Score Python SDK

Official Python client library for the RAIL Score API.
Evaluate AI-generated content across 8 dimensions of Responsible AI.

Sync client:
    >>> from rail_score_sdk import RailScoreClient
    >>> client = RailScoreClient(api_key="rail_xxx...")
    >>> result = client.eval(content="AI should be fair.", mode="basic")

Async client + session:
    >>> from rail_score_sdk import AsyncRAILClient, RAILSession
    >>> async with RAILSession(api_key="rail_xxx", threshold=7.0) as session:
    ...     result = await session.evaluate_turn(
    ...         user_message="Hello",
    ...         assistant_response="Hi there!",
    ...     )

LLM provider wrappers:
    >>> from rail_score_sdk.integrations import RAILOpenAI, RAILAnthropic, RAILGemini
"""

# Sync client (v2 -- requests-based)
from .client import RailScoreClient

# Async client (httpx-based)
from .async_client import AsyncRAILClient

# Policy engine
from .policies import Policy, PolicyEngine, RAILBlockedError
from .policies import EvalResult as PolicyEvalResult

# Session management
from .session import RAILSession, TurnRecord

# Middleware
from .middleware import RAILMiddleware

# Response models (sync client)
from .models import (
    RailScore,
    DimensionScore,
    Issue,
    EvalResult,
    SafeRegenerateResult,
    SafeRegenerateMetadata,
    CreditsBreakdown,
    IterationRecord,
    RailPrompt,
    CriticalContentEvaluation,
    ComplianceScore,
    ComplianceDimensionScore,
    RequirementResult,
    ComplianceIssue,
    RiskClassificationDetail,
    ComplianceResult,
    CrossFrameworkSummary,
    MultiComplianceResult,
    HealthResponse,
)

# Exceptions
from .exceptions import (
    RailScoreError,
    AuthenticationError,
    InsufficientCreditsError,
    InsufficientTierError,
    ValidationError,
    ContentTooHarmfulError,
    SessionExpiredError,
    RateLimitError,
    EvaluationFailedError,
    NotImplementedByServerError,
    ServiceUnavailableError,
)

__version__ = "2.2.1"
__all__ = [
    # Sync client
    "RailScoreClient",
    # Async client
    "AsyncRAILClient",
    # Policy engine
    "Policy",
    "PolicyEngine",
    "PolicyEvalResult",
    "RAILBlockedError",
    # Session
    "RAILSession",
    "TurnRecord",
    # Middleware
    "RAILMiddleware",
    # Eval models
    "RailScore",
    "DimensionScore",
    "Issue",
    "EvalResult",
    # Safe-Regenerate models
    "SafeRegenerateResult",
    "SafeRegenerateMetadata",
    "CreditsBreakdown",
    "IterationRecord",
    "RailPrompt",
    "CriticalContentEvaluation",
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
    # Exceptions
    "RailScoreError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "InsufficientTierError",
    "ValidationError",
    "ContentTooHarmfulError",
    "SessionExpiredError",
    "RateLimitError",
    "EvaluationFailedError",
    "NotImplementedByServerError",
    "ServiceUnavailableError",
]
