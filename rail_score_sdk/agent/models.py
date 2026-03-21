"""
Response models for agent evaluation endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Shared sub-models
# ---------------------------------------------------------------------------

@dataclass
class AgentDimensionScore:
    score: float
    confidence: float
    explanation: Optional[str] = None
    issues: Optional[List[str]] = None


@dataclass
class AgentComplianceViolation:
    framework: str
    article: str
    title: str
    severity: str  # "low" | "medium" | "high" | "critical"
    description: str
    remediation: Optional[str] = None


@dataclass
class AgentPolicyResult:
    """Policy metadata embedded in a tool-call evaluation response."""
    applied_rule: str
    threshold_used: Dict[str, Any]
    violated_dimensions: List[str]
    source: str  # "custom" | "org_custom" | "system_default"


@dataclass
class AgentContextSignals:
    tool_risk_level: str  # "low" | "medium" | "high" | "critical"
    proxy_variables_detected: List[str]
    pii_fields_detected: List[str]
    high_stakes_domain: bool


# ---------------------------------------------------------------------------
# Tool-call evaluation response
# ---------------------------------------------------------------------------

@dataclass
class AgentDecision:
    """Result from client.agent.evaluate_tool_call()."""
    decision: str                                        # "ALLOW" | "FLAG" | "BLOCK"
    decision_reason: str
    event_id: str
    rail_score: Any                                      # RailScore from models.py
    dimension_scores: Dict[str, AgentDimensionScore]
    compliance_violations: List[AgentComplianceViolation]
    policy: AgentPolicyResult
    context_signals: AgentContextSignals
    suggested_params: Optional[Dict[str, Any]] = None
    credits_consumed: float = 0.0
    evaluation_depth: str = "basic"
    evaluated_at: str = ""


# ---------------------------------------------------------------------------
# Tool-result evaluation response
# ---------------------------------------------------------------------------

@dataclass
class PiiEntity:
    type: str
    value: str
    offset: int
    should_redact: bool


@dataclass
class PiiDetection:
    found: bool
    entities: List[PiiEntity]
    redacted_result: Optional[str] = None
    compliance_flags: Optional[List[str]] = None


@dataclass
class InjectionDetection:
    detected: bool
    confidence: float
    patterns_checked: List[str]


@dataclass
class ToolResultRisk:
    """Result from client.agent.evaluate_tool_result()."""
    event_id: str
    risk_level: str           # "low" | "medium" | "high" | "critical"
    recommended_action: str   # "PASS" | "FLAG" | "REDACT_AND_PASS" | "REDACT_AND_FLAG" | "BLOCK"
    pii_detected: Optional[PiiDetection] = None
    prompt_injection: Optional[InjectionDetection] = None
    rail_score: Optional[Dict[str, Any]] = None
    context_signals: Optional[AgentContextSignals] = None
    redacted_available: bool = False
    credits_consumed: float = 0.0
    evaluated_at: str = ""


# ---------------------------------------------------------------------------
# Injection check response
# ---------------------------------------------------------------------------

@dataclass
class InjectionCheck:
    """Result from client.agent.check_injection()."""
    event_id: str
    injection_detected: bool
    confidence: float
    attack_type: str   # "none" | "direct_instruction_override" | "role_hijack" | "jailbreak" | ...
    severity: str      # "none" | "low" | "medium" | "high" | "critical"
    payload_preview: Optional[str] = None
    recommended_action: str = "PASS"
    credits_consumed: float = 0.0
    evaluated_at: str = ""


# ---------------------------------------------------------------------------
# Plan evaluation response
# ---------------------------------------------------------------------------

@dataclass
class PlanStepResult:
    step_index: int
    tool_name: str
    decision: str    # "ALLOW" | "FLAG" | "BLOCK"
    rail_score: float
    dimension_scores: Optional[Dict[str, AgentDimensionScore]] = None
    compliance_violations: Optional[List[AgentComplianceViolation]] = None
    suggested_params: Optional[Dict[str, Any]] = None
    context_signals: Optional[AgentContextSignals] = None


@dataclass
class PlanEvaluation:
    """Result from client.agent.evaluate_plan()."""
    overall_risk: str           # "low" | "medium" | "high" | "critical"
    overall_decision: str       # "ALLOW_ALL" | "PARTIAL_BLOCK" | "BLOCK_ALL"
    plan_summary: str
    step_results: List[PlanStepResult]
    credits_consumed: float = 0.0
    evaluated_at: str = ""


# ---------------------------------------------------------------------------
# Tool registry models
# ---------------------------------------------------------------------------

@dataclass
class ToolRiskProfile:
    tool_name: str
    risk_level: str
    evaluation_depth: str
    source: str  # "system" | "org_custom"
    thresholds: Optional[Dict[str, Any]] = None
    compliance_frameworks: Optional[List[str]] = None
    proxy_variable_watch: Optional[List[str]] = None
    pii_fields_watch: Optional[List[str]] = None
    description: Optional[str] = None


@dataclass
class ToolRegistryPagination:
    total: int
    limit: int
    offset: int
    has_more: bool


@dataclass
class ToolRegistryList:
    tools: List[ToolRiskProfile]
    pagination: ToolRegistryPagination


@dataclass
class RegistryDeleteResult:
    tool_name: str
    deleted: bool
    fallback: str  # "generic" | "system_default"


# ---------------------------------------------------------------------------
# Session models
# ---------------------------------------------------------------------------

@dataclass
class SessionPattern:
    pattern: str       # "repeated_pii_access" | "escalating_risk_scores" | ...
    description: str
    severity: str
    first_seen: str


@dataclass
class ComplianceExposure:
    violations: int
    warnings: int
    risk_tier: Optional[str] = None


@dataclass
class SessionRiskSummary:
    session_id: str
    agent_id: str
    status: str          # "active" | "closed"
    total_tool_calls: int
    allowed: int
    flagged: int
    blocked: int
    critical_violations: int
    current_risk_score: float
    risk_trend: str      # "stable" | "improving" | "escalating" | "critical"
    dimension_averages: Dict[str, float]
    patterns_detected: List[SessionPattern]
    compliance_exposure: Dict[str, ComplianceExposure]
    total_credits_consumed: float
    duration_seconds: Optional[int] = None
    closed_at: Optional[str] = None


@dataclass
class SessionEvent:
    """Single event in session history."""
    type: str        # "tool_call" | "tool_result" | "injection_check"
    tool_name: str
    decision: str
    rail_score: Optional[float]
    event_id: str
    timestamp: str
