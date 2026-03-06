"""
Safe-Regenerate example for RAIL Score Python SDK v2.2.

Demonstrates evaluating content and iteratively regenerating it
until RAIL thresholds are met, using both server-side (RAIL_Safe_LLM)
and client-orchestrated (external) modes.
"""

from rail_score_sdk import RailScoreClient

# Initialize the client
client = RailScoreClient(api_key="your-api-key-here", timeout=120)

print("=" * 70)
print("RAIL Score SDK — Safe-Regenerate Examples")
print("=" * 70)

# --- Example 1: RAIL_Safe_LLM mode (server handles regeneration) ---
print("\nExample 1: RAIL_Safe_LLM mode (server-side regeneration)")
print("-" * 70)

result = client.safe_regenerate(
    content=(
        "Our AI system collects user data. We use it for stuff. "
        "It's fast and works well."
    ),
    mode="basic",
    max_regenerations=2,
    regeneration_model="RAIL_Safe_LLM",
    thresholds={
        "overall": {"score": 8.0, "confidence": 0.5},
        "tradeoff_mode": "priority",
        "max_dimension_failures": 2,
    },
)

print(f"Status: {result.status}")
print(f"Credits consumed: {result.credits_consumed}")

if result.best_content:
    print(f"\nBest content (iteration {result.best_iteration}):")
    print(f"  {result.best_content[:200]}...")

if result.best_scores:
    rail = result.best_scores.get("rail_score", {})
    print(f"\nBest RAIL score: {rail.get('score', 'N/A')}/10")

if result.iteration_history:
    print(f"\nIteration history ({len(result.iteration_history)} iterations):")
    for rec in result.iteration_history:
        scores = rec.scores or {}
        rail = scores.get("rail_score", {})
        print(
            f"  Iteration {rec.iteration}: "
            f"score={rail.get('score', 'N/A')}, "
            f"improvement={rec.improvement_from_previous}"
        )

# --- Example 2: External mode (client-orchestrated) ---
print("\n\nExample 2: External mode (client-orchestrated)")
print("-" * 70)

ext_result = client.safe_regenerate(
    content="Our AI system collects user data. We use it for stuff.",
    mode="basic",
    max_regenerations=1,
    regeneration_model="external",
)

print(f"Status: {ext_result.status}")

if ext_result.status == "awaiting_regeneration":
    print(f"Session ID: {ext_result.session_id}")
    print(f"Iterations remaining: {ext_result.iterations_remaining}")

    if ext_result.rail_prompt:
        print(f"\nRAIL prompt (use this with your own LLM):")
        print(f"  System: {ext_result.rail_prompt.system_prompt[:100]}...")
        print(f"  User: {ext_result.rail_prompt.user_prompt[:100]}...")

    # In a real scenario, you would call your own LLM here with the prompt,
    # then continue the session:
    #
    # improved_content = my_llm_call(ext_result.rail_prompt)
    # continued = client.safe_regenerate_continue(
    #     session_id=ext_result.session_id,
    #     regenerated_content=improved_content,
    # )
    # print(f"Continued status: {continued.status}")

# --- Example 3: Custom thresholds with dimension targets ---
print("\n\nExample 3: Custom dimension thresholds")
print("-" * 70)

result3 = client.safe_regenerate(
    content=(
        "You should never trust anyone over 40 with technology decisions. "
        "Young people just understand the digital world better."
    ),
    mode="basic",
    max_regenerations=2,
    regeneration_model="RAIL_Safe_LLM",
    thresholds={
        "overall": {"score": 7.5},
    },
)

print(f"Status: {result3.status}")
if result3.best_content:
    print(f"Best content: {result3.best_content[:200]}...")
if result3.credits_breakdown:
    cb = result3.credits_breakdown
    print(f"Credits: {cb.evaluations} eval + {cb.regenerations} regen = {cb.total} total")

print("\n" + "=" * 70)
print("Safe-Regenerate Examples Complete!")
print("=" * 70)
