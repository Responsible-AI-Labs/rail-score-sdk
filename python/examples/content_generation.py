"""
Content generation example for RAIL Score Python SDK.

This example shows how to generate content with automatic RAIL quality checks.
"""

from rail_score_sdk import RailScoreClient

# Initialize the client
client = RailScoreClient(
    api_key='your-rail-api-key-here',
    timeout=60  # Longer timeout for generation
)

# Generate content with RAIL requirements
result = client.generate(
    prompt="Write about the importance of ethical AI in financial services",
    length='medium',
    context={
        'purpose': 'blog_post',
        'industry': 'finance',
        'target_audience': 'professionals',
        'tone': 'professional'
    },
    rail_requirements={
        'minimum_scores': {
            'fairness': 8.0,
            'safety': 8.0,
            'reliability': 7.5,
            'transparency': 7.5
        },
        'auto_regenerate': True,
        'max_attempts': 3
    }
)

# Display generated content
print("Generated Content:")
print("=" * 70)
print(result.content)
print("=" * 70)

# Display RAIL scores
print(f"\nRAIL Score: {result.rail_scores.rail_score}/10")
print(f"Requirements Met: {'✅' if result.rail_scores.requirements_met else '❌'}")
print(f"\nGeneration Details:")
print(f"  Model: {result.generation_metadata.model}")
print(f"  Attempts: {result.generation_metadata.attempts}")
print(f"  Time: {result.generation_metadata.generation_time_ms}ms")

# Display dimension scores
print(f"\nDimension Scores:")
for dimension, score in result.rail_scores.dimension_scores.items():
    print(f"  {dimension.capitalize()}: {score}/10")

# Show generation history
if result.generation_history:
    print(f"\nGeneration History: {len(result.generation_history)} attempt(s)")
