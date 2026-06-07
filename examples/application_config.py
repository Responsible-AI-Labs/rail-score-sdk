"""
Application configuration introspection for RAIL Score Python SDK.

Every API key is bound to an application whose governance policy is configured
centrally (evaluation mode, thresholds, dimension weights, enforcement, and
safe-regeneration). These read-only calls let you inspect that configuration at
runtime — useful for startup checks, dashboards, and monitoring. They consume
no credits.
"""

from rail_score_sdk import RailScoreClient

client = RailScoreClient(api_key="your-api-key-here")

# --- 1. Current application configuration ---
cfg = client.get_config()

print(f"Application: {cfg.application.id} ({cfg.application.environment})")
print(f"Organization: {cfg.application.organization}")
print(f"Plan: {cfg.application.plan}")
print()
print("Policy:")
print(f"  enforcement:       {cfg.policy.enforcement}")
print(f"  eval mode:         {cfg.policy.eval_mode}")
print(f"  overall threshold: {cfg.policy.overall_threshold}")
print(f"  locked:            {cfg.policy.locked}")
print(f"  safe regenerate:   {cfg.policy.safe_regenerate}")
print()
print(f"Enforcement mode: {cfg.enforcement.mode}")  # "enforce" or "monitor"

# When a policy is locked in the dashboard, the server applies it and ignores
# any conflicting per-request mode/domain/weights. Detect that from your app:
if cfg.policy.locked:
    print("\nNote: governance policy is locked by an administrator.")

# --- 2. Plan capabilities and request limits ---
caps = client.get_capabilities()
print(f"\nPlan: {caps.plan}")
print(f"Limits: {caps.limits}")

# --- 3. Dimension metadata (weights/thresholds for this application) ---
dims = client.get_dimensions()
print("\nDimensions:")
for d in dims.dimensions:
    print(f"  {d.get('name')}: weight={d.get('weight')} threshold={d.get('threshold')}")
