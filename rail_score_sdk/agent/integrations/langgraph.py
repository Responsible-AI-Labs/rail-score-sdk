"""
LangGraph integration for RAIL Score SDK.

Requires: pip install "rail-score-sdk[langgraph]"
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from ..policy import AgentPolicy
from ..session import AgentSession


class RAILLangGraphGuard:
    """
    LangGraph node and conditional edge router that guards tool calls.

    Add as a node between your planning node and execution node.
    Use ``route`` as the conditional edge function to automatically
    route ALLOW → execute, BLOCK → back to plan.

    Args:
        rail_api_key: RAIL Score API key.
        policy: Policy mode applied to evaluated tool calls.
        domain: Domain hint passed to the RAIL engine.
        compliance_frameworks: Frameworks checked on every call.
        agent_id: Session agent identifier.

    Example::

        from rail_score_sdk.agent.integrations import RAILLangGraphGuard
        from rail_score_sdk.agent import AgentPolicy
        from langgraph.graph import StateGraph, END

        rail_guard = RAILLangGraphGuard(
            rail_api_key="rail_...",
            policy=AgentPolicy.SUGGEST_FIX,
            domain="hr",
        )

        graph = StateGraph(AgentState)
        graph.add_node("plan", plan_node)
        graph.add_node("rail_check", rail_guard.as_node())
        graph.add_node("execute", execute_node)

        graph.add_edge("plan", "rail_check")
        graph.add_conditional_edges(
            "rail_check",
            rail_guard.route,
            {"allow": "execute", "block": "plan", "end": END},
        )
    """

    def __init__(
        self,
        rail_api_key: str,
        policy: AgentPolicy | str = AgentPolicy.LOG_ONLY,
        domain: str = "general",
        compliance_frameworks: Optional[list] = None,
        agent_id: str = "langgraph-agent",
    ) -> None:
        from rail_score_sdk import RailScoreClient

        self._client = RailScoreClient(api_key=rail_api_key)
        self.session = AgentSession(
            self._client,
            agent_id=agent_id,
            compliance_frameworks=compliance_frameworks or [],
        )
        self.domain = domain
        self._policy = policy if isinstance(policy, AgentPolicy) else AgentPolicy(policy)
        self._last_result: Optional[Any] = None

    def as_node(self) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        """Return a LangGraph-compatible node function."""

        def node(state: Dict[str, Any]) -> Dict[str, Any]:
            tool_name = state.get("tool_name", "unknown")
            tool_params = state.get("tool_params", {})

            result = self.session.evaluate_tool_call(
                tool_name=tool_name,
                tool_params=tool_params,
                domain=self.domain,
            )
            self._last_result = result
            return {
                **state,
                "rail_decision": result.decision,
                "rail_score": result.rail_score.score,
                "rail_suggested_params": result.suggested_params,
                "rail_decision_reason": result.decision_reason,
            }

        return node

    def route(self, state: Dict[str, Any]) -> str:
        """Conditional edge function — routes based on RAIL decision."""
        decision = state.get("rail_decision", "ALLOW")
        if decision == "BLOCK":
            if (
                self._policy == AgentPolicy.SUGGEST_FIX
                and state.get("rail_suggested_params")
            ):
                # Inject suggested params and retry planning
                return "block"
            return "end"
        return "allow"
