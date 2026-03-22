"""
AgentMiddleware — decorator-based wrapper for tool-calling functions.

Evaluates tool calls before execution and (optionally) results after
execution.  Analogous to RAILMiddleware for content generation.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Dict, List, Optional

from .exceptions import AgentBlockedError
from .policy import AgentPolicy


class AgentMiddleware:
    """
    Decorator-based RAIL guard for tool-calling functions.

    Wrap any function that calls an external tool.  The middleware evaluates
    the call **before** execution and enforces the configured policy.

    Args:
        client: A :class:`RailScoreClient` instance.
        policy: Policy mode — :class:`AgentPolicy` or string.
            ``"block"``, ``"suggest_fix"``, ``"log_only"``, ``"auto_fix"``.
        default_domain: Domain hint applied to all guarded calls.
        compliance_frameworks: Compliance frameworks checked on every call.
        default_thresholds: Block/flag/dimension thresholds.

    Example::

        middleware = AgentMiddleware(
            client,
            policy=AgentPolicy.BLOCK,
            default_domain="finance",
            compliance_frameworks=["eu_ai_act"],
        )

        @middleware.guard(tool_name="credit_scoring_api")
        def call_credit_api(applicant_id, zip_code, loan_amount, **kwargs):
            return credit_api.score(applicant_id, zip_code, loan_amount)

        try:
            score = call_credit_api(
                applicant_id="u-1234",
                zip_code="90210",
                loan_amount=50000,
            )
        except AgentBlockedError as e:
            print(e.decision_reason)
            if e.suggested_params:
                score = call_credit_api(**e.suggested_params)
    """

    def __init__(
        self,
        client: Any,
        policy: AgentPolicy | str = AgentPolicy.LOG_ONLY,
        default_domain: str = "general",
        compliance_frameworks: Optional[List[str]] = None,
        default_thresholds: Optional[Dict[str, Any]] = None,
    ) -> None:
        if isinstance(policy, str):
            policy = AgentPolicy(policy)
        self._c = client
        self.policy = policy
        self.default_domain = default_domain
        self.compliance_frameworks = compliance_frameworks or []
        self.default_thresholds = default_thresholds

    def guard(
        self,
        tool_name: str,
        domain: Optional[str] = None,
        compliance_frameworks: Optional[List[str]] = None,
        custom_thresholds: Optional[Dict[str, Any]] = None,
        check_result: bool = False,
        result_checks: Optional[List[str]] = None,
    ) -> Callable:
        """
        Decorator that guards a tool-calling function with RAIL evaluation.

        When the decorated function is called:

        1. The middleware extracts ``**kwargs`` as ``tool_params``.
        2. Calls ``client.agent.evaluate_tool_call(tool_name, tool_params)``.
        3. If ``ALLOW`` or ``FLAG`` → executes the original function.
        4. If ``BLOCK``:

           - ``LOG_ONLY`` → executes the original function, logs the block.
           - ``SUGGEST_FIX`` → returns the suggested params, does not execute.
           - ``BLOCK`` → raises :class:`AgentBlockedError`.
           - ``AUTO_FIX`` → retries with ``suggested_params`` if available.

        When ``check_result=True``, also evaluates the function's return value
        via ``client.agent.evaluate_tool_result()``.

        Args:
            tool_name: Tool identifier sent to the RAIL engine.
            domain: Domain override for this tool.
            compliance_frameworks: Override compliance frameworks for this tool.
            custom_thresholds: Override thresholds for this tool.
            check_result: Also evaluate the tool's return value.
            result_checks: Which result checks to run when ``check_result``
                is True.  Defaults to ``["pii", "prompt_injection"]``.

        Returns:
            Decorator.
        """
        effective_domain = domain or self.default_domain
        effective_frameworks = compliance_frameworks or self.compliance_frameworks
        effective_thresholds = custom_thresholds or self.default_thresholds

        def decorator(fn: Callable) -> Callable:
            @functools.wraps(fn)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Combine positional + keyword args as tool params
                tool_params: Dict[str, Any] = dict(kwargs)

                eval_result = self._c.agent.evaluate_tool_call(
                    tool_name=tool_name,
                    tool_params=tool_params,
                    domain=effective_domain,
                    compliance_frameworks=effective_frameworks or None,
                    custom_thresholds=effective_thresholds,
                )

                decision = eval_result.decision

                if decision == "BLOCK":
                    if self.policy == AgentPolicy.BLOCK:
                        raise AgentBlockedError(
                            decision_reason=eval_result.decision_reason,
                            rail_score=eval_result.rail_score.score,
                            violated_dimensions=list(
                                eval_result.policy.violated_dimensions
                            ),
                            suggested_params=eval_result.suggested_params,
                            compliance_violations=eval_result.compliance_violations,
                            event_id=eval_result.event_id,
                        )

                    if self.policy == AgentPolicy.SUGGEST_FIX:
                        raise AgentBlockedError(
                            decision_reason=eval_result.decision_reason,
                            rail_score=eval_result.rail_score.score,
                            violated_dimensions=list(
                                eval_result.policy.violated_dimensions
                            ),
                            suggested_params=eval_result.suggested_params,
                            compliance_violations=eval_result.compliance_violations,
                            event_id=eval_result.event_id,
                        )

                    if self.policy == AgentPolicy.AUTO_FIX:
                        if eval_result.suggested_params:
                            return fn(*args, **eval_result.suggested_params)
                        # No suggestion available — fall through to LOG_ONLY behaviour

                    # LOG_ONLY: proceed but attach eval result
                    result = fn(*args, **kwargs)
                    if hasattr(result, "__dict__"):
                        result.__rail_eval__ = eval_result
                    return result

                # ALLOW or FLAG — execute normally
                result = fn(*args, **kwargs)

                if check_result and result is not None:
                    result_str = str(result) if not isinstance(result, str) else result
                    risk = self._c.agent.evaluate_tool_result(
                        tool_name=tool_name,
                        tool_result=result_str,
                        tool_params=tool_params,
                        checks=result_checks or ["pii", "prompt_injection"],
                    )
                    if hasattr(result, "__dict__"):
                        result.__rail_result_risk__ = risk
                    elif isinstance(result, str) and risk.pii_detected:
                        if (
                            risk.pii_detected.found
                            and risk.pii_detected.redacted_result is not None
                            and self.policy == AgentPolicy.BLOCK
                        ):
                            return risk.pii_detected.redacted_result

                return result

            return wrapper

        return decorator
