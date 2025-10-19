"""
Tone analysis and matching example for RAIL Score Python SDK.

This example shows how to analyze tone from sources and match content to that tone.
"""

from rail_score_sdk import RailScoreClient

# Initialize the client
client = RailScoreClient(
    api_key='your-rail-api-key-here'
)

# Step 1: Analyze tone from sources
print("Step 1: Analyzing tone from sources...")
tone_result = client.analyze_tone(
    sources=[
        {
            'type': 'text',
            'value': '''
                At TechCorp, we believe in innovation that serves humanity.
                Our mission is to create technology that's accessible, ethical,
                and transformative. We're committed to transparency and building
                trust with our customers every step of the way.
            '''
        }
    ],
    create_profile=True,
    profile_name='TechCorp Brand Voice'
)

# Display tone characteristics
tone = tone_result.tone_profile
print(f"\nTone Profile: {tone.name}")
print(f"Profile ID: {tone.profile_id}")
print(f"\nCharacteristics:")
print(f"  Formality: {tone.characteristics.formality:.2f}")
print(f"  Complexity: {tone.characteristics.complexity:.2f}")
print(f"  Emotion: {tone.characteristics.emotion:.2f}")
print(f"  Technical Level: {tone.characteristics.technical_level:.2f}")
print(f"  Voice: {tone.characteristics.voice}")
print(f"  Vocabulary: {tone.characteristics.vocabulary_level}")

# Step 2: Match content to the tone profile
print("\n\nStep 2: Matching content to tone profile...")
content_to_match = """
We have developed a new AI system. It uses machine learning algorithms
to process data. The system has been tested and shows good results.
"""

match_result = client.match_tone(
    content=content_to_match,
    tone_profile_id=tone.profile_id,
    adjustment_level='moderate'
)

# Display matched content
print("\nOriginal Content:")
print("-" * 70)
print(content_to_match)
print("-" * 70)

print("\nMatched Content:")
print("-" * 70)
print(match_result.matched_content)
print("-" * 70)

print(f"\nMatch Score: {match_result.match_score:.2f}")
print(f"\nAdjustments Made:")
for adjustment in match_result.adjustments_made:
    print(f"  • {adjustment}")
