"""
Advanced features example for RAIL Score Python SDK v2.

Demonstrates custom weights, dimension filtering, domain/usecase
parameters, explanations endpoint, and model info.
"""

from rail_score_sdk import RailScoreClient

# Initialize the client
client = RailScoreClient(api_key="your-api-key-here", timeout=60)

print("=" * 70)
print("RAIL Score SDK — Advanced Features")
print("=" * 70)

# --- Example 1: Custom Dimension Weights ---
print("\nExample 1: Custom Dimension Weights")
print("-" * 70)

content = """
Our AI-powered financial advisor helps you make investment decisions
based on your risk profile and financial goals. The system analyzes
market trends and provides personalized recommendations.
"""

# Default weights (equal across all 8 dimensions)
default_result = client.eval(content=content, domain="finance")
print(f"Default weights — Score: {default_result.rail_score.score}/10")

# Custom weights: prioritize safety and reliability for finance
weighted_result = client.eval(
    content=content,
    domain="finance",
    weights={
        "fairness": 10,
        "safety": 25,
        "reliability": 25,
        "transparency": 10,
        "privacy": 10,
        "accountability": 10,
        "inclusivity": 5,
        "user_impact": 5,
    },
)
print(f"Custom weights — Score: {weighted_result.rail_score.score}/10")

# --- Example 2: Single Dimension Evaluation ---
print("\n\nExample 2: Single Dimension Evaluation")
print("-" * 70)

safety_result = client.eval(
    content="Mix bleach and ammonia for a powerful cleaning solution.",
    dimensions=["safety"],
    mode="deep",
)

safety_score = safety_result.dimension_scores["safety"]
print(f"Safety: {safety_score.score}/10")
if safety_score.explanation:
    print(f"Explanation: {safety_score.explanation}")
if safety_score.issues:
    print(f"Issues: {', '.join(safety_score.issues)}")

# --- Example 3: Domain-Specific Evaluation ---
print("\n\nExample 3: Domain-Specific Evaluation")
print("-" * 70)

medical_content = (
    "Take 500mg of ibuprofen every 4 hours for pain relief. "
    "This is safe for everyone including children and pregnant women."
)

for domain in ["general", "healthcare"]:
    result = client.eval(content=medical_content, domain=domain, mode="basic")
    print(f"Domain '{domain}': {result.rail_score.score}/10")

# --- Example 4: Compare Basic vs Deep ---
print("\n\nExample 4: Basic vs Deep Mode Comparison")
print("-" * 70)

test_content = (
    "Women are generally worse at math than men. This is why "
    "STEM fields are dominated by males."
)

basic = client.eval(content=test_content, mode="basic")
deep = client.eval(
    content=test_content,
    mode="deep",
    include_suggestions=True,
)

print(f"Basic: {basic.rail_score.score}/10 (confidence: {basic.rail_score.confidence})")
print(f"Deep:  {deep.rail_score.score}/10 (confidence: {deep.rail_score.confidence})")

if deep.issues:
    print(f"\nIssues found ({len(deep.issues)}):")
    for issue in deep.issues[:5]:
        print(f"  [{issue.dimension}] {issue.description}")

if deep.improvement_suggestions:
    print(f"\nSuggestions:")
    for s in deep.improvement_suggestions[:3]:
        print(f"  - {s}")

print("\n" + "=" * 70)
print("Advanced Features Complete!")
print("=" * 70)
