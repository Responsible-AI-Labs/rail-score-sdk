"""
End-to-end chatbot with OpenAI + RAIL Score evaluation.

Demonstrates a continuous multi-turn chat loop where every assistant
response is automatically scored via RAIL. If the score drops below
the threshold, the response is regenerated using safe-regenerate.

Requirements:
    pip install rail-score-sdk openai

Usage:
    export OPENAI_API_KEY="sk-..."
    export RAIL_API_KEY="rail_..."
    python examples/chatbot_openai.py
"""

import asyncio
import os

from openai import AsyncOpenAI

from rail_score_sdk import AsyncRAILClient


RAIL_API_KEY = os.environ["RAIL_API_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

THRESHOLD = 7.0
MODEL = "gpt-4o-mini"
SYSTEM_PROMPT = (
    "You are a helpful, fair, and safe assistant. "
    "Always provide balanced, evidence-based responses."
)


async def main():
    openai = AsyncOpenAI(api_key=OPENAI_API_KEY)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("=" * 60)
    print("  OpenAI + RAIL Score Chatbot")
    print(f"  Model: {MODEL} | Threshold: {THRESHOLD}")
    print("  Type 'quit' to exit")
    print("=" * 60)

    async with AsyncRAILClient(api_key=RAIL_API_KEY) as rail:
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            if not user_input or user_input.lower() in ("quit", "exit"):
                print("\nGoodbye!")
                break

            messages.append({"role": "user", "content": user_input})

            # Generate response with OpenAI
            completion = await openai.chat.completions.create(
                model=MODEL,
                messages=messages,
            )
            response_text = completion.choices[0].message.content or ""

            # Build context from recent messages for RAIL eval
            context = "\n".join(
                f"{m['role']}: {m['content']}" for m in messages[-6:]
            )

            # RAIL evaluation
            eval_result = await rail.eval(
                content=response_text,
                mode="basic",
                context=context,
                include_issues=True,
            )

            rail_score = eval_result.get("rail_score", {})
            score = rail_score.get("score", 0.0)
            confidence = rail_score.get("confidence", 0.0)

            # Check if response passes threshold
            if score >= THRESHOLD:
                messages.append({"role": "assistant", "content": response_text})
                print(f"\nAssistant: {response_text}")
                print(f"  [RAIL: {score:.1f}/10, confidence: {confidence:.2f}]")
            else:
                # Score too low — attempt safe-regenerate
                print(f"  [RAIL: {score:.1f}/10 — below threshold, regenerating...]")

                regen_result = await rail.safe_regenerate(
                    content=response_text,
                    mode="basic",
                    max_regenerations=1,
                    regeneration_model="RAIL_Safe_LLM",
                    thresholds={"overall": {"score": THRESHOLD}},
                    user_query=user_input,
                )

                regen_data = regen_result.get("result", regen_result)
                best_content = regen_data.get("best_content", response_text)
                best_scores = regen_data.get("best_scores", {})
                new_score = best_scores.get("rail_score", {}).get("score", score)

                messages.append({"role": "assistant", "content": best_content})
                print(f"\nAssistant: {best_content}")
                print(
                    f"  [RAIL: {score:.1f} -> {new_score:.1f}/10, "
                    f"status: {regen_data.get('status', 'unknown')}]"
                )

            # Show dimension scores
            dims = eval_result.get("dimension_scores", {})
            if dims:
                dim_str = " | ".join(
                    f"{d}: {v.get('score', 0)}"
                    for d, v in sorted(dims.items())
                )
                print(f"  [{dim_str}]")


if __name__ == "__main__":
    asyncio.run(main())
