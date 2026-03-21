"""
RAIL Agent Evaluation — SDK v2.4+

Client-side components for evaluating AI agent tool calls against
the 8 RAIL dimensions of Responsible AI.

Quick start (sync)::

    from rail_score_sdk import RailScoreClient

    client = RailScoreClient(api_key="rail_...")
    result = client.agent.evaluate_tool_call(
        tool_name="credit_scoring_api",
        tool_params={"zip_code": "90210", "loan_amount": 50000},
        domain="finance",
    )
    print(result.decision)   # "ALLOW" | "FLAG" | "BLOCK"

Quick start (async)::

    from rail_score_sdk import AsyncRAILClient

    async with AsyncRAILClient(api_key="rail_...") as client:
        result = await client.agent.evaluate_tool_call(
            tool_name="credit_scoring_api",
            tool_params={"zip_code": "90210"},
        )

Session-based tracking::

    from rail_score_sdk.agent import AgentSession

    session = AgentSession(client, agent_id="my-agent")
    result = session.evaluate_tool_call("web_search", {"query": "..."})
    summary = session.risk_summary()

Framework integrations::

    from rail_score_sdk.agent.integrations import (
        RAILCrewAICallback,
        RAILLangGraphGuard,
        RAILAutoGenHook,
    )
"""

from ._client import AgentClient
from ._async_client import AsyncAgentClient
from .session import AgentSession
from .policy import AgentPolicy, AgentPolicyEngine, PolicyCheckResult
from .middleware import AgentMiddleware
from .exceptions import (
    AgentBlockedError,
    PlanBlockedError,
    SessionClosedError,
    AgentSessionExpiredError,
)
from .models import (
    AgentDecision,
    AgentDimensionScore,
    AgentComplianceViolation,
    AgentContextSignals,
    AgentPolicyResult,
    ToolResultRisk,
    PiiDetection,
    PiiEntity,
    InjectionDetection,
    InjectionCheck,
    PlanStepResult,
    PlanEvaluation,
    ToolRiskProfile,
    ToolRegistryList,
    ToolRegistryPagination,
    RegistryDeleteResult,
    SessionPattern,
    ComplianceExposure,
    SessionRiskSummary,
    SessionEvent,
)

__all__ = [
    # Client namespaces
    "AgentClient",
    "AsyncAgentClient",
    # Session
    "AgentSession",
    # Policy
    "AgentPolicy",
    "AgentPolicyEngine",
    "PolicyCheckResult",
    # Middleware
    "AgentMiddleware",
    # Exceptions
    "AgentBlockedError",
    "PlanBlockedError",
    "SessionClosedError",
    "AgentSessionExpiredError",
    # Tool-call models
    "AgentDecision",
    "AgentDimensionScore",
    "AgentComplianceViolation",
    "AgentContextSignals",
    "AgentPolicyResult",
    # Tool-result models
    "ToolResultRisk",
    "PiiDetection",
    "PiiEntity",
    "InjectionDetection",
    # Injection check
    "InjectionCheck",
    # Plan models
    "PlanStepResult",
    "PlanEvaluation",
    # Registry models
    "ToolRiskProfile",
    "ToolRegistryList",
    "ToolRegistryPagination",
    "RegistryDeleteResult",
    # Session models
    "SessionPattern",
    "ComplianceExposure",
    "SessionRiskSummary",
    "SessionEvent",
]
