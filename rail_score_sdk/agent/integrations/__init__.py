"""
Agent framework integrations for RAIL Score SDK.

Drop-in hooks for CrewAI, LangGraph, and AutoGen.

Install extras:
    pip install "rail-score-sdk[crewai]"
    pip install "rail-score-sdk[langgraph]"
    pip install "rail-score-sdk[autogen]"
    pip install "rail-score-sdk[agents]"       # all three
"""

from .crewai import RAILCrewAICallback
from .langgraph import RAILLangGraphGuard
from .autogen import RAILAutoGenHook

__all__ = [
    "RAILCrewAICallback",
    "RAILLangGraphGuard",
    "RAILAutoGenHook",
]
