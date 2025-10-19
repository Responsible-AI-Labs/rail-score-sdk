"""
Basic usage example for RAIL Score Python SDK.

This example shows the most common use case: calculating a RAIL score for content.
"""

from rail_score_sdk import RailScoreClient

# Initialize the client
client = RailScoreClient(
    api_key='your-rail-api-key-here'
)

# Calculate RAIL score for content
content = """
Artificial intelligence has the potential to transform healthcare by improving
diagnostic accuracy and personalizing treatment plans. However, we must ensure
that AI systems are developed responsibly, with careful attention to patient
privacy, data security, and equitable access to these technologies.
"""

result = client.calculate(
    content=content,
    domain='healthcare',
    explain_scores=True
)

# Display results
print(f"RAIL Score: {result.rail_score}/10")
print(f"Grade: {result.grade}")
print(f"\nDimension Scores:")

for dimension, details in result.dimension_scores.items():
    print(f"  {dimension.capitalize()}: {details.score}/10 ({details.grade})")
    if details.suggestions:
        print(f"    Suggestion: {details.suggestions[0]}")

print(f"\nStrengths:")
for strength in result.overall_analysis.strengths:
    print(f"  • {strength}")

print(f"\nWeaknesses:")
for weakness in result.overall_analysis.weaknesses:
    print(f"  • {weakness}")

print(f"\nTop Priority: {result.overall_analysis.top_priority}")
print(f"\nEvaluation completed in {result.evaluation_metadata.evaluation_time_ms}ms")
