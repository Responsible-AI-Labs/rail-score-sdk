"""
Drop-in wrappers for popular LLM providers and observability platforms.

Provider wrappers:
    - RAILOpenAI        -- wraps the ``openai`` Python SDK
    - RAILAnthropic     -- wraps the ``anthropic`` Python SDK
    - RAILGemini        -- wraps the ``google-genai`` SDK

Observability:
    - RAILLangfuse      -- pushes RAIL scores to Langfuse v3
    - RAILGuardrail     -- LiteLLM custom guardrail hook
"""

from rail_score_sdk.integrations.openai_wrapper import RAILOpenAI
from rail_score_sdk.integrations.anthropic_wrapper import RAILAnthropic
from rail_score_sdk.integrations.google_wrapper import RAILGemini
from rail_score_sdk.integrations.langfuse_integration import RAILLangfuse
from rail_score_sdk.integrations.litellm_guardrail import RAILGuardrail

__all__ = [
    "RAILOpenAI",
    "RAILAnthropic",
    "RAILGemini",
    "RAILLangfuse",
    "RAILGuardrail",
]
