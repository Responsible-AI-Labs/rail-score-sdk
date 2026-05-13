"""
Async agent client — namespace attached as `client.agent` on AsyncRAILClient.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .models import (
    InjectionCheck,
    PlanEvaluation,
    PlanStepResult,
    RegistryDeleteResult,
    ToolRegistryList,
    ToolRegistryPagination,
    ToolResultRisk,
    ToolRiskProfile,
)
from ..exceptions import InsufficientTierError
from ._client import (
    _parse_agent_decision,
    _parse_injection_check,
    _parse_tool_result_risk,
    _parse_tool_profile,
    _PLAN_BATCH_HEADER,
)

# ---------------------------------------------------------------------------
# Async registry client
# ---------------------------------------------------------------------------


class AsyncAgentRegistryClient:
    """Async CRUD client for the tool risk registry."""

    def __init__(self, client: Any) -> None:
        self._c = client  # AsyncRAILClient reference

    async def list_tools(
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

        data = await self._c._request(
            "GET", "/railscore/v1/agent/registry/tools", params=params
        )
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

    async def register_tool(
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

        data = await self._c._request(
            "POST", "/railscore/v1/agent/registry/tools", payload=payload
        )
        return _parse_tool_profile(data.get("tool", data))

    async def delete_tool(self, tool_name: str) -> RegistryDeleteResult:
        data = await self._c._request(
            "DELETE", f"/railscore/v1/agent/registry/tools/{tool_name}"
        )
        return RegistryDeleteResult(
            tool_name=tool_name,
            deleted=data.get("deleted", True),
            fallback=data.get("fallback", "generic"),
        )


# ---------------------------------------------------------------------------
# Async agent client
# ---------------------------------------------------------------------------


class AsyncAgentClient:
    """
    Async agent evaluation namespace — available as ``client.agent``
    on :class:`AsyncRAILClient`.

    Example::

        result = await client.agent.evaluate_tool_call(
            tool_name="credit_scoring_api",
            tool_params={"zip_code": "90210", "loan_amount": 50000},
            domain="finance",
        )
        print(result.decision)   # "BLOCK"
    """

    def __init__(self, client: Any) -> None:
        self._c = client  # AsyncRAILClient reference
        self.registry = AsyncAgentRegistryClient(client)

    async def evaluate_tool_call(
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
    ):
        """Evaluate a tool call **before** execution (async)."""
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

        try:
            data = await self._c._request(
                "POST",
                "/railscore/v1/agent/tool-call",
                payload=payload,
                extra_headers=_extra_headers,
            )
        except InsufficientTierError as e:
            if (
                isinstance(getattr(e, "response", None), dict)
                and "decision" in e.response
            ):
                return _parse_agent_decision(e.response)
            raise
        return _parse_agent_decision(data)

    async def evaluate_tool_result(
        self,
        tool_name: str,
        tool_result: Optional[str] = None,
        tool_result_data: Optional[Any] = None,
        tool_params: Optional[Dict[str, Any]] = None,
        checks: Optional[List[str]] = None,
        agent_context: Optional[Dict[str, Any]] = None,
    ) -> ToolResultRisk:
        """Evaluate a tool's output **after** execution (async)."""
        tool_result_obj: Dict[str, Any] = {}
        if tool_result is not None:
            tool_result_obj["raw"] = tool_result
            tool_result_obj["format"] = "text"
        if tool_result_data is not None:
            tool_result_obj["data"] = tool_result_data
            tool_result_obj.setdefault("format", "json")

        payload: Dict[str, Any] = {
            "tool_name": tool_name,
            "tool_result": tool_result_obj,
        }
        if tool_params is not None:
            payload["tool_params"] = tool_params
        if checks is not None:
            payload["checks"] = checks
        if agent_context is not None:
            payload["agent_context"] = agent_context

        data = await self._c._request(
            "POST", "/railscore/v1/agent/tool-result", payload=payload
        )
        return _parse_tool_result_risk(data)

    async def check_injection(
        self,
        content: str,
        content_source: Optional[str] = None,
        agent_context: Optional[Dict[str, Any]] = None,
    ) -> InjectionCheck:
        """Fast standalone prompt-injection check (async)."""
        payload: Dict[str, Any] = {"content": content}
        if content_source is not None:
            payload["content_source"] = content_source
        if agent_context is not None:
            payload["agent_context"] = agent_context

        data = await self._c._request(
            "POST", "/railscore/v1/agent/prompt-injection", payload=payload
        )
        return _parse_injection_check(data)

    async def evaluate_plan(
        self,
        plan: List[Dict[str, Any]],
        goal: str = "",
        agent_id: Optional[str] = None,
        domain: str = "general",
        mode: str = "basic",
        compliance_frameworks: Optional[List[str]] = None,
    ) -> PlanEvaluation:
        """Evaluate a multi-step agent plan before any tool executes (async).

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
            result = await self.evaluate_tool_call(
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
            f"Blocked steps: {blocked}."
            if blocked
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
