"""
CrewAI integration for RAIL Score SDK.

Requires: pip install "rail-score-sdk[crewai]"
"""

from __future__ import annotations

from typing import Any, Optional

from ..policy import AgentPolicy
from ..session import AgentSession


class RAILCrewAICallback:
    """
    CrewAI callback that evaluates every tool call via RAIL Score.

    Attach to a ``Crew`` to automatically guard all tool executions.

    Args:
        rail_api_key: RAIL Score API key.
        policy: Policy mode applied to all tool calls.
        compliance_frameworks: Frameworks checked on every call.
        agent_id: Identifier for the session (used in summaries).

    Example::

        from rail_score_sdk.agent.integrations import RAILCrewAICallback
        from rail_score_sdk.agent import AgentPolicy

        rail_callback = RAILCrewAICallback(
            rail_api_key="rail_...",
            policy=AgentPolicy.BLOCK,
            compliance_frameworks=["eu_ai_act"],
        )

        from crewai import Crew
        crew = Crew(
            agents=[...],
            tasks=[...],
            callbacks=[rail_callback],
        )
        result = crew.kickoff()

        print(rail_callback.session.risk_summary())
    """

    def __init__(
        self,
        rail_api_key: str,
        policy: AgentPolicy | str = AgentPolicy.LOG_ONLY,
        compliance_frameworks: Optional[list] = None,
        agent_id: str = "crewai-agent",
    ) -> None:
        try:
            from rail_score_sdk import RailScoreClient
        except ImportError as exc:
            raise ImportError(
                "rail-score-sdk is required for RAILCrewAICallback."
            ) from exc

        self._client = RailScoreClient(api_key=rail_api_key)
        self.session = AgentSession(
            self._client,
            agent_id=agent_id,
            compliance_frameworks=compliance_frameworks or [],
        )
        self._policy = (
            policy if isinstance(policy, AgentPolicy) else AgentPolicy(policy)
        )

    # CrewAI callback interface
    def on_tool_use(self, tool_name: str, tool_input: Any, **kwargs: Any) -> None:
        """Called by CrewAI before a tool executes."""
        params = tool_input if isinstance(tool_input, dict) else {"input": tool_input}
        try:
            result = self.session.evaluate_tool_call(
                tool_name=tool_name,
                tool_params=params,
            )
            if result.decision == "BLOCK" and self._policy == AgentPolicy.BLOCK:
                from ..exceptions import AgentBlockedError

                raise AgentBlockedError(
                    decision_reason=result.decision_reason,
                    rail_score=result.rail_score.score,
                    suggested_params=result.suggested_params,
                    event_id=result.event_id,
                )
        except Exception:
            if self._policy == AgentPolicy.BLOCK:
                raise

    def on_tool_result(self, tool_name: str, tool_output: Any, **kwargs: Any) -> None:
        """Called by CrewAI after a tool executes."""
        output_str = (
            str(tool_output) if not isinstance(tool_output, str) else tool_output
        )
        self.session.evaluate_tool_result(
            tool_name=tool_name,
            tool_result=output_str,
            checks=["pii", "prompt_injection"],
        )
