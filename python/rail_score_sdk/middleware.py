"""
Provider-agnostic pre/post hooks that any framework can plug into.

The middleware wraps a generic ``generate`` callable and injects
RAIL evaluation + policy enforcement around it.

Usage:
    from rail_score_sdk.middleware import RAILMiddleware

    async def my_llm_call(messages):
        # call any LLM and return the text
        return "LLM response text"

    mw = RAILMiddleware(
        api_key="rail_xxx",
        generate_fn=my_llm_call,
        threshold=7.0,
        policy="regenerate",
    )
    result = await mw.run(messages=[{"role": "user", "content": "Hello"}])
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from rail_score_sdk.async_client import AsyncRAILClient
from rail_score_sdk.policies import EvalResult, Policy, PolicyEngine, RAILBlockedError


# Callable that takes messages and returns generated text
GenerateFn = Callable[..., Awaitable[str]]

# Optional hook signatures
PreHook = Callable[[List[Dict[str, str]]], Awaitable[Optional[List[Dict[str, str]]]]]
PostHook = Callable[[str, EvalResult], Awaitable[None]]


class RAILMiddleware:
    """
    Wraps any async LLM generate function with RAIL evaluation.

    Pipeline:
        1. ``pre_hook`` -- optional async function to inspect / mutate messages
        2. ``generate_fn`` -- your LLM call (OpenAI, Gemini, Anthropic, etc.)
        3. RAIL evaluation
        4. Policy enforcement (block / regenerate / log)
        5. ``post_hook`` -- optional async function for logging / observability

    Parameters
    ----------
    api_key : str
        RAIL Score API key.
    generate_fn : async callable
        Your LLM generation function. Must accept ``messages`` kwarg and
        return the generated text as ``str``.
    threshold : float
        Minimum acceptable RAIL score.
    policy : str or Policy
        Enforcement policy.
    mode : str
        ``"basic"`` or ``"deep"``.
    domain, usecase : str
        Passed to the RAIL eval API.
    pre_hook, post_hook : callable, optional
        Async functions called before / after evaluation.
    eval_input : bool
        If True, also RAIL-evaluate the user's last message before
        calling the LLM (safety gate).
    input_threshold : float
        Separate threshold for input evaluation.
    base_url : str
        Override the RAIL API base URL.
    """

    def __init__(
        self,
        api_key: str,
        generate_fn: GenerateFn,
        *,
        threshold: float = 7.0,
        policy: Union[Policy, str] = Policy.LOG_ONLY,
        mode: str = "basic",
        domain: str = "general",
        usecase: str = "general",
        pre_hook: Optional[PreHook] = None,
        post_hook: Optional[PostHook] = None,
        eval_input: bool = False,
        input_threshold: float = 5.0,
        base_url: str = "https://api.responsibleailabs.ai",
    ) -> None:
        self.generate_fn = generate_fn
        self.threshold = threshold
        self.mode = mode
        self.domain = domain
        self.usecase = usecase
        self.pre_hook = pre_hook
        self.post_hook = post_hook
        self.eval_input = eval_input
        self.input_threshold = input_threshold

        self._client = AsyncRAILClient(api_key=api_key, base_url=base_url)
        self._policy = PolicyEngine(policy=policy, threshold=threshold)

    async def run(
        self,
        messages: List[Dict[str, str]],
        **generate_kwargs: Any,
    ) -> EvalResult:
        """
        Execute the full middleware pipeline.

        Parameters
        ----------
        messages : list[dict]
            Conversation messages in OpenAI-style format:
            ``[{"role": "user", "content": "..."}]``
        **generate_kwargs
            Extra keyword arguments forwarded to ``generate_fn``.

        Returns
        -------
        EvalResult
            The scored (and possibly regenerated) result.
        """
        async with self._client:
            # 1) Pre-hook -----------------------------------------------
            if self.pre_hook is not None:
                modified = await self.pre_hook(messages)
                if modified is not None:
                    messages = modified

            # 2) Input safety gate (optional) ---------------------------
            if self.eval_input and messages:
                last_user = next(
                    (m["content"] for m in reversed(messages) if m.get("role") == "user"),
                    None,
                )
                if last_user:
                    input_eval = await self._client.eval(
                        content=last_user,
                        mode="basic",
                        dimensions=["safety", "fairness"],
                        domain=self.domain,
                    )
                    input_score = input_eval.get("rail_score", {}).get("score", 10)
                    if input_score < self.input_threshold:
                        raise RAILBlockedError(
                            score=input_score,
                            threshold=self.input_threshold,
                            issues=input_eval.get("issues", []),
                        )

            # 3) Generate -----------------------------------------------
            generated_text = await self.generate_fn(messages=messages, **generate_kwargs)

            # 4) RAIL evaluation ----------------------------------------
            context_parts = []
            for m in messages[-5:]:
                context_parts.append(f"{m.get('role', 'user')}: {m.get('content', '')}")
            context_str = "\n".join(context_parts)

            eval_response = await self._client.eval(
                content=generated_text,
                mode=self.mode,
                context=context_str,
                domain=self.domain,
                usecase=self.usecase,
                include_issues=True,
                include_suggestions=True,
            )

            # 5) Policy enforcement -------------------------------------
            result = await self._policy.enforce(
                content=generated_text,
                eval_response=eval_response,
                async_client=self._client,
            )

            # 6) Post-hook (fire and forget is fine) --------------------
            if self.post_hook is not None:
                await self.post_hook(generated_text, result)

        return result
