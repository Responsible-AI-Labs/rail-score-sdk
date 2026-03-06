"""
LiteLLM custom guardrail that evaluates LLM responses via RAIL Score.

Implements the ``CustomGuardrail`` base class from ``litellm`` so it
can be plugged into the LiteLLM proxy as a pre_call / post_call hook.

Setup in ``litellm config.yaml``:

    guardrails:
      - guardrail_name: "rail-score-guard"
        litellm_params:
          guardrail: rail_score_sdk.integrations.litellm_guardrail.RAILGuardrail
          mode: "post_call"
          api_key: os.environ/RAIL_API_KEY
          api_base: os.environ/RAIL_API_BASE

Usage as a standalone hook (without litellm proxy):

    from rail_score_sdk.integrations import RAILGuardrail

    guard = RAILGuardrail(
        api_key="rail_xxx",
        guardrail_name="rail-score",
        event_hook="post_call",
        rail_threshold=7.0,
        rail_mode="basic",
    )
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("rail_score_sdk.litellm")

# RAIL dimensions to check in pre_call (input safety)
_INPUT_DIMENSIONS = ["safety", "fairness"]


def _try_import_litellm():
    """Try importing litellm guardrail base class."""
    try:
        from litellm.integrations.custom_guardrail import CustomGuardrail
        return CustomGuardrail
    except ImportError:
        return None


# Dynamically decide the base class
_LiteLLMBase = _try_import_litellm()


class RAILGuardrail(_LiteLLMBase if _LiteLLMBase is not None else object):
    """
    RAIL Score guardrail for LiteLLM proxy.

    This class works in two modes:

    **pre_call** -- evaluates the user's input for safety/fairness.
    If the score is below ``rail_input_threshold``, the request is blocked.

    **post_call** -- evaluates the LLM's output on all 8 dimensions.
    If the score is below ``rail_threshold``, raises an exception
    (LiteLLM handles the error response).

    Parameters
    ----------
    api_key : str
        RAIL Score API key.
    api_base : str, optional
        Override the RAIL API base URL.
    guardrail_name : str
        Name for this guardrail instance.
    event_hook : str or list[str]
        ``"pre_call"``, ``"post_call"``, or ``"during_call"``.
    default_on : bool
        If True, guardrail runs on all requests by default.
    rail_threshold : float
        Minimum score for LLM output (post_call).
    rail_input_threshold : float
        Minimum score for user input (pre_call).
    rail_mode : str
        ``"basic"`` or ``"deep"``.
    rail_domain : str
        Content domain.
    """

    def __init__(
        self,
        api_key: str = "",
        api_base: str = "https://api.responsibleailabs.ai",
        guardrail_name: str = "rail-score",
        event_hook: Any = "post_call",
        default_on: bool = False,
        rail_threshold: float = 7.0,
        rail_input_threshold: float = 5.0,
        rail_mode: str = "basic",
        rail_domain: str = "general",
        **kwargs: Any,
    ) -> None:
        # Call super if litellm base is available
        if _LiteLLMBase is not None:
            super().__init__(
                guardrail_name=guardrail_name,
                event_hook=event_hook,
                default_on=default_on,
                **kwargs,
            )

        self.api_key = api_key
        self.api_base = api_base
        self.rail_threshold = rail_threshold
        self.rail_input_threshold = rail_input_threshold
        self.rail_mode = rail_mode
        self.rail_domain = rail_domain

    # ------------------------------------------------------------------
    # LiteLLM hook: pre_call -- evaluate user input
    # ------------------------------------------------------------------
    async def async_pre_call_hook(
        self,
        user_api_key_dict: Any,
        cache: Any,
        data: Dict[str, Any],
        call_type: str,
    ) -> Dict[str, Any]:
        """
        Called before the LLM request. Evaluates the user's last message
        for safety and fairness.
        """
        messages = data.get("messages", [])
        if not messages:
            return data

        last_user_msg = next(
            (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
            None,
        )
        if not last_user_msg or len(last_user_msg) < 10:
            return data

        try:
            result = await self._rail_eval(
                content=last_user_msg,
                mode="basic",
                dimensions=_INPUT_DIMENSIONS,
            )
            score = result.get("rail_score", {}).get("score", 10.0)

            if score < self.rail_input_threshold:
                issues = result.get("issues", [])
                issue_text = "; ".join(
                    i.get("description", "") for i in issues[:3]
                )
                raise Exception(
                    f"RAIL Score input blocked (score={score:.1f}, "
                    f"threshold={self.rail_input_threshold}). Issues: {issue_text}"
                )
        except Exception as exc:
            if "RAIL Score input blocked" in str(exc):
                raise
            logger.warning("RAIL pre_call eval failed: %s", exc)

        return data

    # ------------------------------------------------------------------
    # LiteLLM hook: post_call -- evaluate LLM output
    # ------------------------------------------------------------------
    async def async_post_call_success_hook(
        self,
        data: Dict[str, Any],
        user_api_key_dict: Any,
        response: Any,
    ) -> None:
        """
        Called after a successful LLM response. Evaluates the generated
        content on all 8 RAIL dimensions.
        """
        # Extract response text
        content = self._extract_response_text(response)
        if not content or len(content) < 10:
            return

        # Build context from messages
        messages = data.get("messages", [])
        context_parts = [
            f"{m.get('role', 'user')}: {m.get('content', '')}"
            for m in messages[-5:]
        ]

        try:
            result = await self._rail_eval(
                content=content,
                mode=self.rail_mode,
                context="\n".join(context_parts),
            )
            score = result.get("rail_score", {}).get("score", 10.0)

            if score < self.rail_threshold:
                issues = result.get("issues", [])
                issue_text = "; ".join(
                    i.get("description", "") for i in issues[:3]
                )
                raise Exception(
                    f"RAIL Score output blocked (score={score:.1f}, "
                    f"threshold={self.rail_threshold}). Issues: {issue_text}"
                )

            # Attach RAIL metadata to response (for downstream logging)
            if hasattr(response, "_hidden_params"):
                response._hidden_params = response._hidden_params or {}
                headers = response._hidden_params.get("additional_headers", {})
                headers["x-rail-score"] = str(score)
                response._hidden_params["additional_headers"] = headers

        except Exception as exc:
            if "RAIL Score output blocked" in str(exc):
                raise
            logger.warning("RAIL post_call eval failed: %s", exc)

    # ------------------------------------------------------------------
    # LiteLLM hook: during_call (moderation hook, runs parallel to LLM)
    # ------------------------------------------------------------------
    async def async_moderation_hook(
        self,
        data: Dict[str, Any],
        user_api_key_dict: Any,
        call_type: str,
    ) -> None:
        """
        Runs in parallel with the LLM call. Evaluates the user's input.
        Same logic as pre_call but non-blocking to the LLM request.
        """
        messages = data.get("messages", [])
        if not messages:
            return

        last_user_msg = next(
            (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
            None,
        )
        if not last_user_msg or len(last_user_msg) < 10:
            return

        try:
            result = await self._rail_eval(
                content=last_user_msg,
                mode="basic",
                dimensions=_INPUT_DIMENSIONS,
            )
            score = result.get("rail_score", {}).get("score", 10.0)
            if score < self.rail_input_threshold:
                raise Exception(
                    f"RAIL Score moderation blocked (score={score:.1f})"
                )
        except Exception as exc:
            if "RAIL Score moderation blocked" in str(exc):
                raise
            logger.warning("RAIL moderation hook failed: %s", exc)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _rail_eval(
        self,
        content: str,
        mode: str = "basic",
        dimensions: Optional[List[str]] = None,
        context: str = "",
    ) -> Dict[str, Any]:
        """Call the RAIL eval API using httpx (no persistent client needed)."""
        try:
            from litellm.llms.custom_httpx.http_handler import get_async_httpx_client
            from litellm.types.llms.custom_http import httpxSpecialProvider

            client = get_async_httpx_client(
                llm_provider=httpxSpecialProvider.LoggingCallback
            )
        except ImportError:
            import httpx
            client = httpx.AsyncClient(timeout=30.0)

        payload: Dict[str, Any] = {
            "content": content,
            "mode": mode,
            "domain": self.rail_domain,
            "include_issues": True,
        }
        if dimensions:
            payload["dimensions"] = dimensions
        if context:
            payload["context"] = context

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        resp = await client.post(
            f"{self.api_base}/railscore/v1/eval",
            headers=headers,
            json=payload,
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("result", data)

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        """Extract text content from a LiteLLM response object."""
        try:
            # ModelResponse from litellm
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    return choice.message.content or ""
            # Fallback: string response
            if isinstance(response, str):
                return response
        except Exception:
            pass
        return ""
