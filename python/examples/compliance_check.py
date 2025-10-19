"""
Compliance checking example for RAIL Score Python SDK.

This example demonstrates how to check content compliance against
various regulatory frameworks (GDPR, HIPAA, NIST, SOC 2).
"""

from rail_score_sdk import RailScoreClient

# Initialize the client
client = RailScoreClient(
    api_key='your-rail-api-key-here'
)

# Example 1: GDPR Compliance Check
print("=" * 60)
print("Example 1: GDPR Compliance Check")
print("=" * 60)

privacy_policy = """
We collect your name, email address, and usage data to provide our services.
Your data is stored securely and we will not share it with third parties
without your consent. You have the right to access, modify, or delete your
data at any time by contacting us at privacy@example.com.
"""

gdpr_result = client.check_compliance(
    content=privacy_policy,
    framework='gdpr',
    context_type='privacy_policy',
    check_consent=True,
    check_data_minimization=True
)

print(f"\nCompliance Status: {gdpr_result.compliance_status}")
print(f"Overall Score: {gdpr_result.overall_score}/10")
print(f"\nCriteria Scores:")
for criterion, score in gdpr_result.criteria_scores.items():
    print(f"  {criterion}: {score}/10")

if gdpr_result.violations:
    print(f"\nViolations Found:")
    for violation in gdpr_result.violations:
        print(f"  - {violation['description']}")
        print(f"    Severity: {violation['severity']}")

print(f"\nRecommendations:")
for recommendation in gdpr_result.recommendations:
    print(f"  • {recommendation}")

# Example 2: HIPAA Compliance Check
print("\n" + "=" * 60)
print("Example 2: HIPAA Compliance Check (Healthcare)")
print("=" * 60)

healthcare_content = """
Patient records are stored in encrypted databases with access controls.
All staff members undergo annual privacy training. We implement physical
safeguards including locked storage areas and visitor logs. Patient
information is only shared with authorized healthcare providers for
treatment purposes.
"""

hipaa_result = client.check_compliance(
    content=healthcare_content,
    framework='hipaa',
    context_type='policy_document',
    check_phi_handling=True,
    check_access_controls=True
)

print(f"\nCompliance Status: {hipaa_result.compliance_status}")
print(f"Overall Score: {hipaa_result.overall_score}/10")
print(f"\nCriteria Scores:")
for criterion, score in hipaa_result.criteria_scores.items():
    print(f"  {criterion}: {score}/10")

# Example 3: NIST Compliance Check
print("\n" + "=" * 60)
print("Example 3: NIST Cybersecurity Framework Check")
print("=" * 60)

security_policy = """
Our organization implements multi-factor authentication for all user accounts.
We conduct regular security audits and vulnerability assessments. Incident
response procedures are documented and tested quarterly. All systems are
patched monthly and critical vulnerabilities are addressed within 24 hours.
Network traffic is monitored continuously for anomalies.
"""

nist_result = client.check_compliance(
    content=security_policy,
    framework='nist',
    context_type='security_policy',
    check_access_control=True,
    check_incident_response=True
)

print(f"\nCompliance Status: {nist_result.compliance_status}")
print(f"Overall Score: {nist_result.overall_score}/10")
print(f"\nTop Criteria Scores:")
for criterion, score in list(nist_result.criteria_scores.items())[:5]:
    print(f"  {criterion}: {score}/10")

# Example 4: SOC 2 Compliance Check
print("\n" + "=" * 60)
print("Example 4: SOC 2 Compliance Check")
print("=" * 60)

soc2_content = """
Our infrastructure is hosted in SOC 2 certified data centers. We maintain
comprehensive audit logs of all system access and changes. Customer data
is encrypted both in transit and at rest using industry-standard algorithms.
Access to production systems requires approval and is reviewed monthly.
We conduct third-party security assessments annually.
"""

soc2_result = client.check_compliance(
    content=soc2_content,
    framework='soc2',
    context_type='system_description',
    check_security=True,
    check_availability=True,
    check_confidentiality=True
)

print(f"\nCompliance Status: {soc2_result.compliance_status}")
print(f"Overall Score: {soc2_result.overall_score}/10")
print(f"\nCriteria Scores:")
for criterion, score in soc2_result.criteria_scores.items():
    print(f"  {criterion}: {score}/10")

if soc2_result.recommendations:
    print(f"\nTop Recommendations:")
    for i, recommendation in enumerate(soc2_result.recommendations[:3], 1):
        print(f"  {i}. {recommendation}")

# Example 5: Comparative Analysis
print("\n" + "=" * 60)
print("Example 5: Comparative Compliance Analysis")
print("=" * 60)

comprehensive_policy = """
Our organization is committed to data protection and security. We implement
encryption, access controls, and regular security audits. Patient data is
handled according to HIPAA requirements. We comply with GDPR for EU users,
providing data access and deletion rights. Annual third-party assessments
ensure our SOC 2 compliance. All systems follow NIST cybersecurity framework
guidelines.
"""

print("\nChecking compliance across multiple frameworks...")

frameworks = ['gdpr', 'hipaa', 'nist', 'soc2']
results = {}

for framework in frameworks:
    try:
        result = client.check_compliance(
            content=comprehensive_policy,
            framework=framework,
            context_type='comprehensive_policy'
        )
        results[framework] = result.overall_score
        print(f"  {framework.upper()}: {result.overall_score}/10 ({result.compliance_status})")
    except Exception as e:
        print(f"  {framework.upper()}: Error - {str(e)}")

# Find best and worst compliance
if results:
    best_framework = max(results, key=results.get)
    worst_framework = min(results, key=results.get)

    print(f"\nBest Compliance: {best_framework.upper()} ({results[best_framework]}/10)")
    print(f"Needs Improvement: {worst_framework.upper()} ({results[worst_framework]}/10)")

print("\n" + "=" * 60)
print("Compliance Check Complete!")
print("=" * 60)
