"""
Compliance checking example for RAIL Score Python SDK v2.

Demonstrates single-framework, multi-framework, and strict mode compliance
checks against GDPR, CCPA, HIPAA, EU AI Act, India DPDP, and India AI Gov.
"""

from rail_score_sdk import RailScoreClient

# Initialize the client
client = RailScoreClient(api_key="your-api-key-here")

# --- Example 1: GDPR Compliance Check ---
print("=" * 60)
print("Example 1: GDPR Compliance Check")
print("=" * 60)

gdpr_result = client.compliance_check(
    content=(
        "Our AI model processes user browsing history and purchase patterns "
        "to generate personalized product recommendations. We collect IP "
        "addresses, device fingerprints, and cross-site tracking data "
        "without explicit consent."
    ),
    framework="gdpr",
    context={
        "domain": "e-commerce",
        "data_types": ["browsing_history", "purchase_data", "ip_address"],
        "processing_purpose": "personalized_recommendations",
    },
)

print(f"\nScore: {gdpr_result.compliance_score.score}/10 ({gdpr_result.compliance_score.label})")
print(f"Summary: {gdpr_result.compliance_score.summary}")
print(f"Requirements: {gdpr_result.requirements_passed}/{gdpr_result.requirements_checked} passed")

if gdpr_result.issues:
    print(f"\nTop Issues:")
    for issue in gdpr_result.issues[:3]:
        print(f"  [{issue.severity.upper()}] {issue.description}")
        print(f"    Article: {issue.article} | Effort: {issue.remediation_effort}")

# --- Example 2: Multi-Framework Check (GDPR + CCPA) ---
print("\n" + "=" * 60)
print("Example 2: Multi-Framework (GDPR + CCPA)")
print("=" * 60)

multi_result = client.compliance_check(
    content=(
        "We use cookies to track user behavior across websites and sell "
        "aggregated profiles to third-party advertisers. Users can opt out "
        "via a link buried in our privacy policy footer."
    ),
    frameworks=["gdpr", "ccpa"],
    context={
        "domain": "advertising",
        "data_types": ["cookies", "behavioral_data", "user_profiles"],
    },
)

# multi_result is a MultiComplianceResult
summary = multi_result.cross_framework_summary
print(f"\nFrameworks evaluated: {summary.frameworks_evaluated}")
print(f"Average score: {summary.average_score}/10")
print(f"Weakest: {summary.weakest_framework} ({summary.weakest_score}/10)")

for fw_name, fw_result in multi_result.results.items():
    cs = fw_result.compliance_score
    print(f"\n  {fw_name.upper()}: {cs.score}/10 ({cs.label})")
    print(f"    {fw_result.requirements_passed}/{fw_result.requirements_checked} passed")

# --- Example 3: HIPAA with PHI Context ---
print("\n" + "=" * 60)
print("Example 3: HIPAA Compliance Check")
print("=" * 60)

hipaa_result = client.compliance_check(
    content=(
        "Patient records are stored in encrypted databases with access "
        "controls. All staff members undergo annual privacy training. "
        "Patient information is only shared with authorized healthcare "
        "providers for treatment purposes."
    ),
    framework="hipaa",
    context={
        "domain": "healthcare",
        "data_types": ["phi"],
        "processing_purpose": "treatment",
    },
)

print(f"\nScore: {hipaa_result.compliance_score.score}/10 ({hipaa_result.compliance_score.label})")
print(f"Requirements: {hipaa_result.requirements_passed}/{hipaa_result.requirements_checked} passed")

if hipaa_result.improvement_suggestions:
    print(f"\nSuggestions:")
    for s in hipaa_result.improvement_suggestions[:3]:
        print(f"  - {s}")

# --- Example 4: EU AI Act (High-Risk System) ---
print("\n" + "=" * 60)
print("Example 4: EU AI Act — Risk Classification")
print("=" * 60)

ai_act_result = client.compliance_check(
    content=(
        "Our facial recognition system is deployed in public spaces for "
        "real-time surveillance. It identifies individuals without their "
        "knowledge. No risk assessment was conducted before deployment."
    ),
    framework="eu_ai_act",
    context={
        "domain": "law_enforcement",
        "system_type": "biometric_identification",
        "data_types": ["biometric_data", "facial_images"],
        "risk_indicators": [
            "real_time_surveillance",
            "biometric_identification",
            "law_enforcement",
        ],
    },
)

print(f"\nScore: {ai_act_result.compliance_score.score}/10 ({ai_act_result.compliance_score.label})")

if ai_act_result.risk_classification_detail:
    rd = ai_act_result.risk_classification_detail
    print(f"Risk Tier: {rd.tier}")
    print(f"Basis: {rd.basis}")

# --- Example 5: Strict Mode ---
print("\n" + "=" * 60)
print("Example 5: Strict Mode (higher threshold)")
print("=" * 60)

strict_result = client.compliance_check(
    content=(
        "Our AI chatbot provides general customer service. It uses "
        "anonymized data and identifies itself as AI. Users can request "
        "human support. Conversations are encrypted and deleted after 30 days."
    ),
    framework="ccpa",
    strict_mode=True,
    context={"domain": "customer_service"},
)

print(f"\nScore: {strict_result.compliance_score.score}/10 ({strict_result.compliance_score.label})")
print(f"Strict mode threshold: 8.5")
print(f"Requirements: {strict_result.requirements_passed}/{strict_result.requirements_checked} passed")
print(f"Warnings: {strict_result.requirements_warned}")

print("\n" + "=" * 60)
print("Compliance Checks Complete!")
print("=" * 60)
