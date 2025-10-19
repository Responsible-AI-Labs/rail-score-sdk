"""
Content regeneration example for RAIL Score Python SDK.

This example demonstrates how to improve existing content by regenerating it
with specific RAIL dimension improvements.
"""

from rail_score_sdk import RailScoreClient

# Initialize the client
client = RailScoreClient(
    api_key='your-rail-api-key-here',
    timeout=60  # Longer timeout for regeneration
)

print("=" * 70)
print("RAIL Score SDK - Content Regeneration Examples")
print("=" * 70)

# Example 1: Basic Content Regeneration
print("\nExample 1: Basic Content Regeneration")
print("-" * 70)

original_content = """
Our AI system uses advanced algorithms to analyze data.
It's fast and efficient. The system has been tested and works well.
Users can access it through our platform.
"""

print("Original Content:")
print(original_content)

# Regenerate with improvements
result = client.regenerate(
    original_content=original_content,
    improve_dimensions=['fairness', 'transparency', 'inclusivity'],
    user_notes="Make the content more professional and detailed",
    keep_structure=True,
    keep_tone=False  # Allow tone to change for improvement
)

print("\nRegenerated Content:")
print("-" * 70)
print(result.content)
print("-" * 70)

# Show improvements
print("\nDimension Improvements:")
for dimension, improvement in result.improvements.items():
    print(f"  {dimension.capitalize()}:")
    print(f"    Before: {improvement.before:.1f}/10")
    print(f"    After:  {improvement.after:.1f}/10")
    print(f"    Change: +{improvement.improvement:.1f}")

print(f"\nChanges Made:")
for change in result.changes_made:
    print(f"  • {change}")

# Example 2: Improving Specific Weaknesses
print("\n\nExample 2: Improving Specific Weaknesses")
print("-" * 70)

# First, calculate RAIL score to identify weaknesses
weak_content = """
The system analyzes user behavior to show relevant ads.
It collects data automatically and uses it for predictions.
This helps companies maximize their revenue.
"""

print("Step 1: Identify weaknesses")
print("Original Content:")
print(weak_content)

initial_score = client.calculate(
    content=weak_content,
    domain='general',
    explain_scores=True
)

print(f"\nInitial RAIL Score: {initial_score.rail_score}/10 ({initial_score.grade})")
print(f"\nWeaknesses identified:")
for weakness in initial_score.overall_analysis.weaknesses[:3]:
    print(f"  • {weakness}")

# Find dimensions with lowest scores
low_scoring_dims = sorted(
    initial_score.dimension_scores.items(),
    key=lambda x: x[1].score
)[:3]

dimensions_to_improve = [dim for dim, _ in low_scoring_dims]

print(f"\nDimensions to improve: {', '.join(dimensions_to_improve)}")

# Step 2: Regenerate to improve these dimensions
print("\nStep 2: Regenerating content...")

improved_result = client.regenerate(
    original_content=weak_content,
    improve_dimensions=dimensions_to_improve,
    user_notes="Address privacy concerns and be more transparent about data usage",
    keep_structure=True,
    keep_tone=True
)

print("\nImproved Content:")
print("-" * 70)
print(improved_result.content)
print("-" * 70)

print(f"\nImprovements by Dimension:")
for dim in dimensions_to_improve:
    if dim in improved_result.improvements:
        imp = improved_result.improvements[dim]
        print(f"  {dim.capitalize()}: {imp.before:.1f} → {imp.after:.1f} (+{imp.improvement:.1f})")

# Example 3: Iterative Improvement
print("\n\nExample 3: Iterative Improvement")
print("-" * 70)

content_v1 = """
Machine learning models can make predictions based on historical data.
They learn patterns and apply them to new situations.
This technology is being used in many industries.
"""

print("Version 1 (Original):")
print(content_v1)

# First iteration: Improve fairness and accountability
print("\nIteration 1: Improving fairness and accountability...")
result_v2 = client.regenerate(
    original_content=content_v1,
    improve_dimensions=['fairness', 'accountability'],
    user_notes="Add information about bias and verification",
    keep_structure=True,
    keep_tone=True
)

content_v2 = result_v2.content
print("\nVersion 2:")
print(content_v2)

# Second iteration: Further improve transparency and privacy
print("\nIteration 2: Improving transparency and privacy...")
result_v3 = client.regenerate(
    original_content=content_v2,
    improve_dimensions=['transparency', 'privacy'],
    user_notes="Explain how the models work and how data is protected",
    keep_structure=True,
    keep_tone=True
)

content_v3 = result_v3.content
print("\nVersion 3 (Final):")
print("-" * 70)
print(content_v3)
print("-" * 70)

# Calculate final score
final_score = client.calculate(
    content=content_v3,
    domain='general',
    explain_scores=False
)

print(f"\nFinal RAIL Score: {final_score.rail_score}/10 ({final_score.grade})")

# Example 4: Preserving Structure vs Tone
print("\n\nExample 4: Preserving Structure vs Tone")
print("-" * 70)

original = """
AI in Healthcare:
1. Diagnosis: AI can analyze medical images
2. Treatment: Personalized treatment plans
3. Research: Drug discovery and development
"""

print("Original (structured list):")
print(original)

# Preserve structure but allow tone change
print("\nRegeneration A: Preserve structure, change tone...")
result_a = client.regenerate(
    original_content=original,
    improve_dimensions=['reliability', 'safety'],
    user_notes="Make it more professional and detailed",
    keep_structure=True,   # Keep the numbered list
    keep_tone=False        # Allow tone to change
)

print("\nResult A (structure preserved, professional tone):")
print(result_a.content)

# Allow structure change but preserve tone
print("\n\nRegeneration B: Change structure, preserve tone...")
result_b = client.regenerate(
    original_content=original,
    improve_dimensions=['transparency', 'user_impact'],
    user_notes="Add more context and explanation",
    keep_structure=False,  # Allow structure to change
    keep_tone=True         # Keep original tone
)

print("\nResult B (structure changed, tone preserved):")
print(result_b.content)

# Example 5: Multi-Dimension Improvement
print("\n\nExample 5: Comprehensive Multi-Dimension Improvement")
print("-" * 70)

blog_post = """
AI is changing the world. Companies are using AI to automate tasks and
increase efficiency. This technology will impact many jobs in the future.
Everyone should learn about AI to stay relevant.
"""

print("Original Blog Post:")
print(blog_post)

# Improve across all weak dimensions
result = client.regenerate(
    original_content=blog_post,
    improve_dimensions=[
        'fairness',       # Remove bias
        'safety',         # Add safeguards
        'reliability',    # Add factual backing
        'transparency',   # Explain how/why
        'inclusivity',    # Make it accessible
        'user_impact'     # Consider audience
    ],
    user_notes="""
    Make this more balanced and nuanced:
    - Acknowledge both benefits and challenges
    - Provide specific examples
    - Consider diverse perspectives
    - Add data/sources where possible
    - Make it accessible to non-technical readers
    """,
    keep_structure=False,
    keep_tone=False
)

print("\nImproved Blog Post:")
print("-" * 70)
print(result.content)
print("-" * 70)

print(f"\nOverall Improvements:")
for dim, score in result.overall_scores.items():
    print(f"  {dim.capitalize()}: {score:.1f}/10")

print(f"\nTotal Changes: {len(result.changes_made)}")
print(f"Key Changes:")
for change in result.changes_made[:5]:  # Show first 5 changes
    print(f"  • {change}")

# Best Practices
print("\n" + "=" * 70)
print("Best Practices for Content Regeneration")
print("=" * 70)
print("""
1. Calculate RAIL score first to identify specific weaknesses
2. Target 2-4 dimensions at a time for focused improvements
3. Provide clear, specific user_notes for better results
4. Use keep_structure=True for maintaining format (lists, sections)
5. Use keep_tone=True for consistent brand voice
6. Consider iterative improvements for complex content
7. Review changes_made to understand what was improved
8. Compare before/after scores to measure improvement
9. Test with your specific domain (healthcare, finance, etc.)
10. Validate improved content still meets your requirements

Structure vs Tone:
- keep_structure=True: Maintains format, layout, organization
- keep_tone=True: Preserves formality, emotion, voice
- Both can be combined or used independently
""")

print("=" * 70)
print("Content Regeneration Examples Complete!")
print("=" * 70)
