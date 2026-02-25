"""
Protected content example for RAIL Score Python SDK v2.

Demonstrates evaluating content against a quality threshold and
regenerating improved content when needed.
"""

from rail_score_sdk import RailScoreClient

# Initialize the client
client = RailScoreClient(api_key="your-api-key-here", timeout=60)

print("=" * 70)
print("RAIL Score SDK — Protected Content Examples")
print("=" * 70)

# --- Example 1: Evaluate against threshold ---
print("\nExample 1: Evaluate content against threshold")
print("-" * 70)

eval_result = client.protected_evaluate(
    content=(
        "You should never trust anyone over 40 with technology decisions. "
        "Young people just understand the digital world better."
    ),
    threshold=7.0,
    mode="basic",
)

print(f"Score: {eval_result.rail_score.score}/10")
print(f"Threshold met: {eval_result.threshold_met}")
print(f"Improvement needed: {eval_result.improvement_needed}")

if eval_result.improvement_prompt:
    print(f"\nImprovement prompt:")
    print(f"  {eval_result.improvement_prompt[:200]}...")

# --- Example 2: Regenerate improved content ---
print("\n\nExample 2: Regenerate improved content")
print("-" * 70)

regen_result = client.protected_regenerate(
    content="You should never trust anyone over 40 with technology decisions.",
    issues_to_fix={
        "fairness": {
            "score": 2.0,
            "explanation": "Age-based discrimination and stereotyping.",
            "issues": ["Age-based stereotyping", "Discriminatory generalization"],
        },
        "inclusivity": {
            "score": 2.5,
            "explanation": "Exclusionary language targeting older adults.",
            "issues": ["Ageist framing"],
        },
    },
)

print(f"Improved content:")
print(f"  {regen_result.improved_content}")
print(f"\nIssues addressed: {', '.join(regen_result.issues_addressed)}")

if regen_result.metadata:
    m = regen_result.metadata
    print(f"Model: {m.model} | Tokens: {m.input_tokens} in / {m.output_tokens} out")

# --- Example 3: Full evaluate-then-regenerate workflow ---
print("\n\nExample 3: Full evaluate → regenerate workflow")
print("-" * 70)

content = (
    "Our AI system uses advanced algorithms to analyze data. "
    "It's fast and efficient. The system has been tested and works well."
)

# Step 1: Evaluate
eval_r = client.protected_evaluate(
    content=content,
    threshold=7.5,
    mode="deep",
)

print(f"Initial score: {eval_r.rail_score.score}/10")

if eval_r.improvement_needed:
    print("Content needs improvement — regenerating...")

    # Build issues_to_fix from dimension scores if available
    issues = {}
    if eval_r.dimension_scores:
        for dim, score in eval_r.dimension_scores.items():
            if score.score < 7.0:
                issues[dim] = {
                    "score": score.score,
                    "explanation": score.explanation or "",
                    "issues": score.issues or [],
                }

    # Step 2: Regenerate
    regen_r = client.protected_regenerate(
        content=content,
        issues_to_fix=issues if issues else None,
    )
    print(f"\nImproved content:")
    print(f"  {regen_r.improved_content}")
else:
    print("Content meets threshold — no regeneration needed.")

print("\n" + "=" * 70)
print("Protected Content Examples Complete!")
print("=" * 70)
