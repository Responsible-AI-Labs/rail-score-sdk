"""
RAIL Score Python SDK

Official Python client library for the RAIL Score API.
Evaluate AI-generated content across 8 dimensions of Responsible AI.

Sync client:
    >>> from rail_score_sdk import RailScoreClient
    >>> client = RailScoreClient(api_key="your-rail-api-key...")
    >>> result = client.eval(content="AI should be fair.", mode="basic")

Async client + session:
    >>> from rail_score_sdk import AsyncRAILClient, RAILSession
    >>> async with RAILSession(api_key="your-rail-api-key", threshold=7.0) as session:
    ...     result = await session.evaluate_turn(
    ...         user_message="Hello",
    ...         assistant_response="Hi there!",
    ...     )

Agent evaluation:
    >>> from rail_score_sdk import RailScoreClient
    >>> from rail_score_sdk.agent import AgentSession, AgentPolicy
    >>> client = RailScoreClient(api_key="your-rail-api-key...")
    >>> result = client.agent.evaluate_tool_call(
    ...     tool_name="credit_scoring_api",
    ...     tool_params={"zip_code": "90210", "loan_amount": 50000},
    ...     domain="finance",
    ... )

LLM provider wrappers:
    >>> from rail_score_sdk.integrations import RAILOpenAI, RAILAnthropic, RAILGemini
"""

__version__ = "2.6.0"

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

# Agent evaluation (v2.4+)
from .agent import (
    AgentSession,
    AgentPolicy,
    AgentPolicyEngine,
    AgentMiddleware,
    AgentBlockedError,
    PlanBlockedError,
    SessionClosedError,
    AgentDecision,
    ToolResultRisk,
    InjectionCheck,
    PlanEvaluation,
    SessionRiskSummary,
)

# DPDP compliance (v2.5+)
from .compliance.dpdp import (
    DPDPCompliance,
    DPDPConfig,
    DPDPContentScanner,
    DPDPContentResult,
    DPDPViolation,
    DPDPPiiMatch,
    DPDPChildSignal,
    DPDPScanResult,
    DPDPDecision,
    DPDPEmitResult,
    DPDPRequireResult,
    DPDPEvidenceArtefact,
    DPDPSession,
    DPDPTimerList,
    DPDPAuditResult,
    DPDPError,
    DPDPBlockedError,
    DPDPHostedOnlyError,
)

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
    # Agent evaluation (v2.4+)
    "AgentSession",
    "AgentPolicy",
    "AgentPolicyEngine",
    "AgentMiddleware",
    "AgentBlockedError",
    "PlanBlockedError",
    "SessionClosedError",
    "AgentDecision",
    "ToolResultRisk",
    "InjectionCheck",
    "PlanEvaluation",
    "SessionRiskSummary",
    # DPDP compliance (v2.5+)
    "DPDPCompliance",
    "DPDPConfig",
    "DPDPContentScanner",
    "DPDPContentResult",
    "DPDPViolation",
    "DPDPPiiMatch",
    "DPDPChildSignal",
    "DPDPScanResult",
    "DPDPDecision",
    "DPDPEmitResult",
    "DPDPRequireResult",
    "DPDPEvidenceArtefact",
    "DPDPSession",
    "DPDPTimerList",
    "DPDPAuditResult",
    "DPDPError",
    "DPDPBlockedError",
    "DPDPHostedOnlyError",
]
