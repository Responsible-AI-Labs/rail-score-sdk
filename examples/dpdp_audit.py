"""
India DPDP — System audit with tiered compliance scoring.

Demonstrates Mode C: system-level audit that evaluates overall DPDP
compliance with tiered requirements and penalty exposure calculation.
"""

from rail_score_sdk import RailScoreClient

client = RailScoreClient(api_key="your-rail-api-key")

# --- Audit as a regular Data Fiduciary ---
print("=" * 60)
print("Audit: Data Fiduciary — Finance Sector")
print("=" * 60)

result = client.dpdp.dpdp_audit(
    content=(
        "Our fintech platform processes Aadhaar numbers for KYC verification. "
        "We collect mobile numbers, PAN cards, and bank account details. "
        "User consent is obtained via checkbox during onboarding. "
        "Data is stored in AWS Mumbai region with encryption at rest."
    ),
    entity_type="data_fiduciary",
    sector="finance",
)

print(f"Overall: {result.overall_label} (score: {result.overall_score})")
if hasattr(result, "tier_1_score") and result.tier_1_score is not None:
    print(f"Tier 1 (Core obligations): {result.tier_1_score}")
if hasattr(result, "tier_2_score") and result.tier_2_score is not None:
    print(f"Tier 2 (Enhanced obligations): {result.tier_2_score}")
if hasattr(result, "tier_3_score") and result.tier_3_score is not None:
    print(f"Tier 3 (Sector-specific): {result.tier_3_score}")
if hasattr(result, "total_penalty_exposure_crore") and result.total_penalty_exposure_crore is not None:
    print(f"Penalty exposure: Rs.{result.total_penalty_exposure_crore} Cr")

# --- Audit as Significant Data Fiduciary ---
print("\n" + "=" * 60)
print("Audit: Significant Data Fiduciary — Healthcare")
print("=" * 60)

result2 = client.dpdp.dpdp_audit(
    content=(
        "Our healthcare AI platform processes patient records including "
        "Aadhaar, medical history, and genetic data. We use AI for "
        "diagnosis assistance. Patient consent is verbal only. "
        "Data is shared with insurance partners without explicit consent."
    ),
    entity_type="significant_data_fiduciary",
    sector="healthcare",
)

print(f"Overall: {result2.overall_label} (score: {result2.overall_score})")

# --- Compliance check (text-based, using existing framework) ---
print("\n" + "=" * 60)
print("Traditional Compliance Check (framework: india_dpdp)")
print("=" * 60)

traditional = client.compliance_check(
    content=(
        "Our platform collects Aadhaar and PAN data for identity verification. "
        "Consent is obtained digitally. Data is encrypted and stored in India."
    ),
    framework="india_dpdp",
    context={"domain": "finance"},
)

print(f"Score: {traditional.compliance_score.score}/10 ({traditional.compliance_score.label})")
print(f"Requirements: {traditional.requirements_passed}/{traditional.requirements_checked} passed")
