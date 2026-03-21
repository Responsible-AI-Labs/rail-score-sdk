"""
Sync agent client — namespace attached as `client.agent` on RailScoreClient.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..models import RailScore
from .models import (
    AgentComplianceViolation,
    AgentContextSignals,
    AgentDecision,
    AgentDimensionScore,
    AgentPolicyResult,
    InjectionCheck,
    InjectionDetection,
    PiiDetection,
    PiiEntity,
    PlanEvaluation,
    PlanStepResult,
    RegistryDeleteResult,
    ToolRegistryList,
    ToolRegistryPagination,
    ToolResultRisk,
    ToolRiskProfile,
)


# ---------------------------------------------------------------------------
# Shared parsing helpers (used by both sync and async clients)
# ---------------------------------------------------------------------------

def _parse_rail_score(data: Dict[str, Any]) -> RailScore:
    return RailScore(
        score=data.get("score", 0.0),
        confidence=data.get("confidence", 0.0),
        summary=data.get("summary", ""),
    )


def _parse_dimension_scores(data: Dict[str, Any]) -> Dict[str, AgentDimensionScore]:
    return {
        dim: AgentDimensionScore(
            score=info.get("score", 0.0),
            confidence=info.get("confidence", 0.0),
            explanation=info.get("explanation"),
            issues=info.get("issues"),
        )
        for dim, info in data.items()
    }


def _parse_compliance_violations(
    data: Optional[List[Dict[str, Any]]],
) -> List[AgentComplianceViolation]:
    if not data:
        return []
    return [
        AgentComplianceViolation(
            framework=v.get("framework", ""),
            article=v.get("article", ""),
            title=v.get("title", ""),
            severity=v.get("severity", "low"),
            description=v.get("description", ""),
            remediation=v.get("remediation"),
        )
        for v in data
    ]


def _parse_policy_result(data: Dict[str, Any]) -> AgentPolicyResult:
    return AgentPolicyResult(
        applied_rule=data.get("applied_rule", ""),
        threshold_used=data.get("threshold_used", {}),
        violated_dimensions=data.get("violated_dimensions", []),
        source=data.get("source", "system_default"),
    )


def _parse_context_signals(data: Dict[str, Any]) -> AgentContextSignals:
    return AgentContextSignals(
        tool_risk_level=data.get("tool_risk_level", "medium"),
        proxy_variables_detected=data.get("proxy_variables_detected", []),
        pii_fields_detected=data.get("pii_fields_detected", []),
        high_stakes_domain=data.get("high_stakes_domain", False),
    )


def _parse_agent_decision(data: Dict[str, Any]) -> AgentDecision:
    return AgentDecision(
        decision=data.get("decision", "ALLOW"),
        decision_reason=data.get("decision_reason", ""),
        event_id=data.get("event_id", ""),
        rail_score=_parse_rail_score(data.get("rail_score", {})),
        dimension_scores=_parse_dimension_scores(data.get("dimension_scores", {})),
        compliance_violations=_parse_compliance_violations(
            data.get("compliance_violations")
        ),
        policy=_parse_policy_result(data.get("policy", {})),
        context_signals=_parse_context_signals(data.get("context_signals", {})),
        suggested_params=data.get("suggested_params"),
        credits_consumed=data.get("credits_consumed", 0.0),
        evaluation_depth=data.get("evaluation_depth", "basic"),
        evaluated_at=data.get("evaluated_at", ""),
    )


def _parse_pii_detection(data: Optional[Dict[str, Any]]) -> Optional[PiiDetection]:
    if data is None:
        return None
    entities = [
        PiiEntity(
            type=e.get("type", ""),
            value=e.get("value", ""),
            offset=e.get("offset", 0),
            should_redact=e.get("should_redact", False),
        )
        for e in data.get("entities", [])
    ]
    return PiiDetection(
        found=data.get("found", False),
        entities=entities,
        redacted_result=data.get("redacted_result"),
        compliance_flags=data.get("compliance_flags"),
    )


def _parse_injection_detection(
    data: Optional[Dict[str, Any]],
) -> Optional[InjectionDetection]:
    if data is None:
        return None
    return InjectionDetection(
        detected=data.get("detected", False),
        confidence=data.get("confidence", 0.0),
        patterns_checked=data.get("patterns_checked", []),
    )


def _parse_tool_result_risk(data: Dict[str, Any]) -> ToolResultRisk:
    cs_raw = data.get("context_signals")
    return ToolResultRisk(
        event_id=data.get("event_id", ""),
        risk_level=data.get("risk_level", "low"),
        recommended_action=data.get("recommended_action", "PASS"),
        pii_detected=_parse_pii_detection(data.get("pii_detected")),
        prompt_injection=_parse_injection_detection(data.get("prompt_injection")),
        rail_score=data.get("rail_score"),
        context_signals=_parse_context_signals(cs_raw) if cs_raw else None,
        redacted_available=data.get("redacted_available", False),
        credits_consumed=data.get("credits_consumed", 0.0),
        evaluated_at=data.get("evaluated_at", ""),
    )


def _parse_injection_check(data: Dict[str, Any]) -> InjectionCheck:
    return InjectionCheck(
        event_id=data.get("event_id", ""),
        injection_detected=data.get("injection_detected", False),
        confidence=data.get("confidence", 0.0),
        attack_type=data.get("attack_type", "none"),
        severity=data.get("severity", "none"),
        payload_preview=data.get("payload_preview"),
        recommended_action=data.get("recommended_action", "PASS"),
        credits_consumed=data.get("credits_consumed", 0.0),
        evaluated_at=data.get("evaluated_at", ""),
    )


def _parse_plan_step(data: Dict[str, Any]) -> PlanStepResult:
    cs_raw = data.get("context_signals")
    return PlanStepResult(
        step_index=data.get("step_index", 0),
        tool_name=data.get("tool_name", ""),
        decision=data.get("decision", "ALLOW"),
        rail_score=data.get("rail_score", 0.0),
        dimension_scores=(
            _parse_dimension_scores(data["dimension_scores"])
            if data.get("dimension_scores")
            else None
        ),
        compliance_violations=_parse_compliance_violations(
            data.get("compliance_violations")
        ) or None,
        suggested_params=data.get("suggested_params"),
        context_signals=_parse_context_signals(cs_raw) if cs_raw else None,
    )


def _parse_tool_profile(data: Dict[str, Any]) -> ToolRiskProfile:
    return ToolRiskProfile(
        tool_name=data["tool_name"],
        risk_level=data.get("risk_level", "medium"),
        evaluation_depth=data.get("evaluation_depth", "basic"),
        source=data.get("source", "org_custom"),
        thresholds=data.get("thresholds"),
        compliance_frameworks=data.get("compliance_frameworks"),
        proxy_variable_watch=data.get("proxy_variable_watch"),
        pii_fields_watch=data.get("pii_fields_watch"),
        description=data.get("description"),
    )


# ---------------------------------------------------------------------------
# Registry client (sync)
# ---------------------------------------------------------------------------

class AgentRegistryClient:
    """CRUD client for the tool risk registry."""

    def __init__(self, client: Any) -> None:
        self._c = client  # RailScoreClient reference

    def list_tools(
        self,
        limit: int = 50,
        offset: int = 0,
        source: str = "all",
        risk_level: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ToolRegistryList:
        params: Dict[str, Any] = {"limit": limit, "offset": offset, "source": source}
        if risk_level is not None:
            params["risk_level"] = risk_level
        if search is not None:
            params["search"] = search

        data = self._c._request("GET", "/agent/registry/tools", params=params)
        tools = [_parse_tool_profile(t) for t in data.get("tools", [])]
        pag = data.get("pagination", {})
        return ToolRegistryList(
            tools=tools,
            pagination=ToolRegistryPagination(
                total=pag.get("total", 0),
                limit=pag.get("limit", limit),
                offset=pag.get("offset", offset),
                has_more=pag.get("has_more", False),
            ),
        )

    def register_tool(
        self,
        tool_name: str,
        risk_level: str = "medium",
        evaluation_depth: str = "basic",
        thresholds: Optional[Dict[str, Any]] = None,
        compliance_frameworks: Optional[List[str]] = None,
        proxy_variable_watch: Optional[List[str]] = None,
        pii_fields_watch: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> ToolRiskProfile:
        payload: Dict[str, Any] = {
            "tool_name": tool_name,
            "risk_level": risk_level,
            "evaluation_depth": evaluation_depth,
        }
        if thresholds is not None:
            payload["thresholds"] = thresholds
        if compliance_frameworks is not None:
            payload["compliance_frameworks"] = compliance_frameworks
        if proxy_variable_watch is not None:
            payload["proxy_variable_watch"] = proxy_variable_watch
        if pii_fields_watch is not None:
            payload["pii_fields_watch"] = pii_fields_watch
        if description is not None:
            payload["description"] = description

        data = self._c._request("POST", "/agent/registry/tools", json=payload)
        return _parse_tool_profile(data.get("tool", data))

    def delete_tool(self, tool_name: str) -> RegistryDeleteResult:
        data = self._c._request("DELETE", f"/agent/registry/tools/{tool_name}")
        return RegistryDeleteResult(
            tool_name=tool_name,
            deleted=data.get("deleted", True),
            fallback=data.get("fallback", "generic"),
        )


# ---------------------------------------------------------------------------
# Agent client (sync)
# ---------------------------------------------------------------------------

_PLAN_BATCH_HEADER = {"X-RAIL-Plan-Batch": "true"}


class AgentClient:
    """
    Sync agent evaluation namespace — available as ``client.agent``.

    Example::

        result = client.agent.evaluate_tool_call(
            tool_name="credit_scoring_api",
            tool_params={"zip_code": "90210", "loan_amount": 50000},
            domain="finance",
        )
        print(result.decision)   # "BLOCK"
    """

    def __init__(self, client: Any) -> None:
        self._c = client  # RailScoreClient reference
        self.registry = AgentRegistryClient(client)

    # ------------------------------------------------------------------
    # evaluate_tool_call
    # ------------------------------------------------------------------

    def evaluate_tool_call(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        agent_context: Optional[Dict[str, Any]] = None,
        domain: str = "general",
        mode: str = "basic",
        compliance_frameworks: Optional[List[str]] = None,
        custom_thresholds: Optional[Dict[str, Any]] = None,
        *,
        _extra_headers: Optional[Dict[str, str]] = None,
    ) -> AgentDecision:
        """Evaluate a tool call **before** execution.

        Args:
            tool_name: Name of the tool being called.
            tool_params: Parameters that would be passed to the tool.
            agent_context: Optional context dict with keys such as
                ``goal``, ``agent_id``, ``prior_tool_calls``, ``turn_index``.
            domain: Content domain — ``general``, ``finance``, ``hr``,
                ``healthcare``, ``legal``, ``code``, etc.
            mode: ``"basic"`` (fast, 1.5 credits) or ``"deep"`` (3 credits).
            compliance_frameworks: Compliance frameworks to check against.
            custom_thresholds: Override block/flag thresholds and dimension
                minimums, e.g.
                ``{"block_below": 5.0, "flag_below": 7.0,
                   "dimension_minimums": {"fairness": 6.0}}``.

        Returns:
            :class:`AgentDecision` with ``decision``, ``rail_score``,
            ``dimension_scores``, ``compliance_violations``,
            and ``suggested_params``.
        """
        payload: Dict[str, Any] = {
            "tool_name": tool_name,
            "tool_params": tool_params,
            "domain": domain,
            "mode": mode,
        }
        if agent_context is not None:
            payload["agent_context"] = agent_context
        if compliance_frameworks is not None:
            payload["compliance_frameworks"] = compliance_frameworks
        if custom_thresholds is not None:
            payload["custom_thresholds"] = custom_thresholds

        data = self._c._request(
            "POST",
            "/agent/tool-call",
            json=payload,
            extra_headers=_extra_headers,
        )
        return _parse_agent_decision(data)

    # ------------------------------------------------------------------
    # evaluate_tool_result
    # ------------------------------------------------------------------

    def evaluate_tool_result(
        self,
        tool_name: str,
        tool_result: Optional[str] = None,
        tool_result_data: Optional[Any] = None,
        tool_params: Optional[Dict[str, Any]] = None,
        checks: Optional[List[str]] = None,
        agent_context: Optional[Dict[str, Any]] = None,
    ) -> ToolResultRisk:
        """Evaluate a tool's output **after** execution.

        Args:
            tool_name: Name of the tool that produced the result.
            tool_result: Raw string result from the tool.
            tool_result_data: Structured result data (dict/list).
            tool_params: Original parameters passed to the tool.
            checks: Which checks to run — any of
                ``"pii"``, ``"prompt_injection"``, ``"rail_score"``.
                Defaults to all three.
            agent_context: Optional agent context dict.

        Returns:
            :class:`ToolResultRisk` with ``risk_level``,
            ``recommended_action``, ``pii_detected``, and
            ``prompt_injection``.
        """
        payload: Dict[str, Any] = {"tool_name": tool_name}
        if tool_result is not None:
            payload["tool_result"] = tool_result
        if tool_result_data is not None:
            payload["tool_result_data"] = tool_result_data
        if tool_params is not None:
            payload["tool_params"] = tool_params
        if checks is not None:
            payload["checks"] = checks
        if agent_context is not None:
            payload["agent_context"] = agent_context

        data = self._c._request("POST", "/agent/tool-result", json=payload)
        return _parse_tool_result_risk(data)

    # ------------------------------------------------------------------
    # check_injection
    # ------------------------------------------------------------------

    def check_injection(
        self,
        content: str,
        content_source: Optional[str] = None,
        agent_context: Optional[Dict[str, Any]] = None,
    ) -> InjectionCheck:
        """Fast standalone prompt-injection check (0.5 credits).

        Args:
            content: Text to check for injection patterns.
            content_source: Where the content came from, e.g.
                ``"web_search_result"``, ``"api_response"``,
                ``"user_input"``.
            agent_context: Optional agent context dict.

        Returns:
            :class:`InjectionCheck` with ``injection_detected``,
            ``confidence``, ``attack_type``, and ``severity``.
        """
        payload: Dict[str, Any] = {"content": content}
        if content_source is not None:
            payload["content_source"] = content_source
        if agent_context is not None:
            payload["agent_context"] = agent_context

        data = self._c._request("POST", "/agent/prompt-injection", json=payload)
        return _parse_injection_check(data)

    # ------------------------------------------------------------------
    # evaluate_plan
    # ------------------------------------------------------------------

    def evaluate_plan(
        self,
        plan: List[Dict[str, Any]],
        goal: str = "",
        agent_id: Optional[str] = None,
        domain: str = "general",
        mode: str = "basic",
        compliance_frameworks: Optional[List[str]] = None,
    ) -> PlanEvaluation:
        """Evaluate a multi-step agent plan before any tool executes.

        Loops over plan steps and calls ``/agent/tool-call`` per step
        with the ``X-RAIL-Plan-Batch: true`` header (discounted credits).

        Args:
            plan: List of step dicts, each with keys:
                ``step_index``, ``tool_name``, ``tool_params``,
                and optionally ``rationale``.
            goal: High-level goal of the plan (used as agent context).
            agent_id: Identifier for the agent executing the plan.
            domain: Content domain hint applied to all steps.
            mode: ``"basic"`` (1.0 credit/step) or
                ``"deep"`` (2.0 credits/step).
            compliance_frameworks: Frameworks to check against all steps.

        Returns:
            :class:`PlanEvaluation` with ``overall_decision``,
            ``overall_risk``, and per-step ``step_results``.

        Raises:
            ValueError: If plan exceeds 20 steps.
        """
        if len(plan) > 20:
            raise ValueError(
                f"Plan has {len(plan)} steps; maximum is 20. "
                "Evaluate in chunks or use session-based tracking."
            )

        step_results: List[PlanStepResult] = []
        total_credits = 0.0
        evaluated_at = ""

        agent_context: Dict[str, Any] = {"goal": goal}
        if agent_id is not None:
            agent_context["agent_id"] = agent_id

        for step in plan:
            result = self.evaluate_tool_call(
                tool_name=step["tool_name"],
                tool_params=step.get("tool_params", {}),
                agent_context={
                    **agent_context,
                    "step_index": step.get("step_index", 0),
                    "rationale": step.get("rationale", ""),
                },
                domain=domain,
                mode=mode,
                compliance_frameworks=compliance_frameworks,
                _extra_headers=_PLAN_BATCH_HEADER,
            )
            total_credits += result.credits_consumed
            if not evaluated_at:
                evaluated_at = result.evaluated_at

            step_results.append(
                PlanStepResult(
                    step_index=step.get("step_index", len(step_results)),
                    tool_name=step["tool_name"],
                    decision=result.decision,
                    rail_score=result.rail_score.score,
                    dimension_scores=result.dimension_scores,
                    compliance_violations=result.compliance_violations or None,
                    suggested_params=result.suggested_params,
                    context_signals=result.context_signals,
                )
            )

        decisions = [s.decision for s in step_results]
        blocked = [s.step_index for s in step_results if s.decision == "BLOCK"]

        if all(d == "BLOCK" for d in decisions):
            overall_decision = "BLOCK_ALL"
        elif any(d == "BLOCK" for d in decisions):
            overall_decision = "PARTIAL_BLOCK"
        else:
            overall_decision = "ALLOW_ALL"

        scores = [s.rail_score for s in step_results]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        if avg_score >= 7.0:
            overall_risk = "low"
        elif avg_score >= 5.0:
            overall_risk = "medium"
        elif avg_score >= 3.0:
            overall_risk = "high"
        else:
            overall_risk = "critical"

        allow_count = sum(1 for d in decisions if d == "ALLOW")
        plan_summary = (
            f"{allow_count} of {len(step_results)} steps can proceed. "
            f"Blocked steps: {blocked}." if blocked
            else f"All {len(step_results)} steps can proceed."
        )

        return PlanEvaluation(
            overall_risk=overall_risk,
            overall_decision=overall_decision,
            plan_summary=plan_summary,
            step_results=step_results,
            credits_consumed=total_credits,
            evaluated_at=evaluated_at,
        )
