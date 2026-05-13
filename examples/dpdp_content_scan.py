"""
India DPDP Content Scan — PII masking and child signal detection.

Demonstrates Mode A: client-side content scanning with DPDPConfig
for PII detection/masking and child signal detection.
No API calls required for local scanning.
"""

from rail_score_sdk.compliance.dpdp import DPDPConfig, DPDPContentScanner

# --- 1. Configure the scanner ---
config = DPDPConfig(
    entity_type="data_fiduciary",
    sector="finance",
    pii_action="mask",
    processes_children=True,
    child_content_action="block",
)
scanner = DPDPContentScanner(config)

# --- 2. Scan text for Indian PII ---
print("=" * 60)
print("PII Detection and Masking")
print("=" * 60)

text = "Customer Aadhaar: 2234 5678 9012, PAN: ABCDE1234F, UPI: user@ybl"
result = scanner.scan_text(text)

print(f"PII found: {len(result.pii_found)}")
for pii in result.pii_found:
    print(f"  {pii.type}: {pii.value} -> {pii.masked_value}")

masked_text, result = scanner.apply_actions(result, text)
print(f"\nOriginal:  {text}")
print(f"Masked:    {masked_text}")

# --- 3. Child signal detection ---
print("\n" + "=" * 60)
print("Child Signal Detection")
print("=" * 60)

child_text = "I am 12 years old and I need help with my homework"
child_result = scanner.scan_text(child_text)

print(f"Child signals: {len(child_result.child_signals)}")
for sig in child_result.child_signals:
    print(f"  {sig.signal_type}: {sig.evidence}")
    if sig.detected_age:
        print(f"    Detected age: {sig.detected_age}")
    print(f"    DPDP section: {sig.section}")

print(f"Session flags: {child_result.session_flags}")

# --- 4. Child targeting protection ---
print("\n" + "=" * 60)
print("Child Targeting Protection")
print("=" * 60)

targeting_text = "Based on their browsing activity, we recommend this product for purchase"
targeting_result = scanner.scan_text(
    targeting_text,
    session_flags=["child_data_detected"],
)

print(f"Violations: {len(targeting_result.violations)}")
for v in targeting_result.violations:
    print(f"  [{v.severity}] {v.check}: {v.reason}")
    print(f"    Action: {v.action} | Section: {v.section}")

processed, targeting_result = scanner.apply_actions(targeting_result, targeting_text)
print(f"Result: {processed}")

# --- 5. Purpose drift detection ---
print("\n" + "=" * 60)
print("Purpose Drift Detection")
print("=" * 60)

drift_config = DPDPConfig(
    purpose="service_delivery",
    purpose_drift_action="warn",
    pii_action="mask",
)
drift_scanner = DPDPContentScanner(drift_config)

drift_text = "We will sell data to third-party advertisers for targeted campaigns"
drift_result = drift_scanner.scan_text(drift_text)

drift_violations = [v for v in drift_result.violations if v.check == "purpose_drift"]
print(f"Drift violations: {len(drift_violations)}")
for v in drift_violations:
    print(f"  {v.reason}")
    print(f"  Action: {v.action}")
