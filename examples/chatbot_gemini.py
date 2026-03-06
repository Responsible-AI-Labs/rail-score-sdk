"""
End-to-end chatbot using the RAILGemini wrapper.

The RAILGemini wrapper auto-evaluates every Gemini response via RAIL
Score and applies the configured policy (log, block, or regenerate).

Requirements:
    pip install rail-score-sdk google-genai

Usage:
    export GEMINI_API_KEY="AIza..."
    export RAIL_API_KEY="rail_..."
    python examples/chatbot_gemini.py
"""

import asyncio
import os

from rail_score_sdk.integrations import RAILGemini
from rail_score_sdk.policies import Policy


RAIL_API_KEY = os.environ["RAIL_API_KEY"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

MODEL = "gemini-2.5-flash"
THRESHOLD = 7.0


async def main():
    # The wrapper handles RAIL eval + policy enforcement automatically
    client = RAILGemini(
        rail_api_key=RAIL_API_KEY,
        gemini_api_key=GEMINI_API_KEY,
        rail_threshold=THRESHOLD,
        rail_policy=Policy.LOG_ONLY,   # log scores, don't block
        rail_mode="basic",
        rail_domain="general",
    )

    history = []

    print("=" * 60)
    print("  Gemini + RAIL Score Chatbot (RAILGemini wrapper)")
    print(f"  Model: {MODEL} | Threshold: {THRESHOLD}")
    print("  Type 'quit' to exit")
    print("=" * 60)

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input or user_input.lower() in ("quit", "exit"):
            print("\nGoodbye!")
            break

        # Build conversation for Gemini
        history.append(f"User: {user_input}")
        prompt = "\n".join(history[-10:])  # last 10 turns as context

        # Generate + auto-evaluate via RAIL
        response = await client.generate(
            model=MODEL,
            contents=prompt,
        )

        history.append(f"Assistant: {response.content}")

        # Print response with RAIL metadata
        print(f"\nAssistant: {response.content}")
        print(
            f"  [RAIL: {response.rail_score:.1f}/10 | "
            f"threshold met: {response.threshold_met} | "
            f"regenerated: {response.was_regenerated}]"
        )

        # Show per-dimension breakdown
        if response.rail_dimensions:
            dims = response.rail_dimensions
            for dim_name, dim_data in sorted(dims.items()):
                dim_score = dim_data.get("score", 0) if isinstance(dim_data, dict) else dim_data
                print(f"    {dim_name}: {dim_score}")

        # Show issues if any
        if response.rail_issues:
            print(f"  Issues ({len(response.rail_issues)}):")
            for issue in response.rail_issues[:3]:
                desc = issue.get("description", str(issue)) if isinstance(issue, dict) else str(issue)
                print(f"    - {desc}")

        # Warn if below threshold
        if not response.threshold_met:
            print(f"  WARNING: Score {response.rail_score:.1f} is below threshold {THRESHOLD}")


if __name__ == "__main__":
    asyncio.run(main())
