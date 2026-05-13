"""
AutoGen integration for RAIL Score SDK.

Requires: pip install "rail-score-sdk[autogen]"
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..policy import AgentPolicy
from ..session import AgentSession


class RAILAutoGenHook:
    """
    AutoGen tool-call hook that evaluates calls via RAIL Score.

    Attach to an ``AssistantAgent`` via ``tool_call_hooks``.

    Args:
        rail_api_key: RAIL Score API key.
        policy: Policy mode applied to all tool calls.
        compliance_frameworks: Frameworks checked on every call.
        agent_id: Session agent identifier.

    Example::

        from rail_score_sdk.agent.integrations import RAILAutoGenHook
        from rail_score_sdk.agent import AgentPolicy
        from autogen import AssistantAgent

        rail_hook = RAILAutoGenHook(
            rail_api_key="rail_...",
            policy=AgentPolicy.LOG_ONLY,
        )

        agent = AssistantAgent(
            name="finance-agent",
            tool_call_hooks=[rail_hook],
        )
    """

    def __init__(
        self,
        rail_api_key: str,
        policy: AgentPolicy | str = AgentPolicy.LOG_ONLY,
        compliance_frameworks: Optional[List[str]] = None,
        agent_id: str = "autogen-agent",
    ) -> None:
        from rail_score_sdk import RailScoreClient

        self._client = RailScoreClient(api_key=rail_api_key)
        self.session = AgentSession(
            self._client,
            agent_id=agent_id,
            compliance_frameworks=compliance_frameworks or [],
        )
        self._policy = (
            policy if isinstance(policy, AgentPolicy) else AgentPolicy(policy)
        )

    # AutoGen hook interface
    def __call__(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        **kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """Called by AutoGen before a tool executes.

        Returns:
            ``None`` to proceed with execution, or a replacement result dict
            to skip execution (used for AUTO_FIX mode with suggested params).
        """
        result = self.session.evaluate_tool_call(
            tool_name=tool_name,
            tool_params=tool_args,
        )

        if result.decision == "BLOCK":
            if self._policy == AgentPolicy.BLOCK:
                from ..exceptions import AgentBlockedError

                raise AgentBlockedError(
                    decision_reason=result.decision_reason,
                    rail_score=result.rail_score.score,
                    suggested_params=result.suggested_params,
                    event_id=result.event_id,
                )
            if self._policy == AgentPolicy.AUTO_FIX and result.suggested_params:
                # Return suggested params as the new args for the tool
                return result.suggested_params

        return None  # proceed with original execution
