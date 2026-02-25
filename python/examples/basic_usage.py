"""
Basic usage example for RAIL Score Python SDK v2.

Shows the most common use cases: basic eval and deep eval with explanations.
"""

from rail_score_sdk import RailScoreClient

# Initialize the client
client = RailScoreClient(api_key="your-api-key-here")

# --- 1. Basic evaluation (all 8 dimensions) ---
content = """
Artificial intelligence has the potential to transform healthcare by improving
diagnostic accuracy and personalizing treatment plans. However, we must ensure
that AI systems are developed responsibly, with careful attention to patient
privacy, data security, and equitable access to these technologies.
"""

result = client.eval(content=content, mode="basic")

print(f"RAIL Score: {result.rail_score.score}/10")
print(f"Summary: {result.rail_score.summary}")
print(f"Confidence: {result.rail_score.confidence}")
print(f"\nDimension Scores:")

for dimension, score in result.dimension_scores.items():
    print(f"  {dimension}: {score.score}/10 (confidence: {score.confidence})")

# --- 2. Deep evaluation with explanations and issues ---
deep_result = client.eval(
    content="Take 500mg of ibuprofen every 4 hours for pain relief.",
    mode="deep",
    dimensions=["safety", "reliability"],
    domain="healthcare",
    include_suggestions=True,
)

print(f"\nDeep Evaluation: {deep_result.rail_score.summary}")
for dimension, score in deep_result.dimension_scores.items():
    print(f"\n  {dimension}: {score.score}/10")
    if score.explanation:
        print(f"    Explanation: {score.explanation}")
    if score.issues:
        print(f"    Issues: {', '.join(score.issues)}")

if deep_result.improvement_suggestions:
    print("\nImprovement Suggestions:")
    for suggestion in deep_result.improvement_suggestions:
        print(f"  - {suggestion}")
