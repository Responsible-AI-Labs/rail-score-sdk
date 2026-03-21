"""
OpenTelemetry observability example for RAIL Score Python SDK.

Demonstrates:
  1. RAILTelemetry setup — console and OTLP exporter options
  2. Project-scoped telemetry for multiple projects in the same org
  3. ComplianceLogger — structured logs for compliance check results
  4. IncidentLogger — raise tracked incidents on threshold breaches
  5. HumanReviewQueue — per-dimension queue for low-scoring content

Install the telemetry extra before running:
    pip install "rail-score-sdk[telemetry]"
"""

import os
from rail_score_sdk import RailScoreClient
from rail_score_sdk.telemetry import (
    RAILTelemetry,
    ComplianceLogger,
    IncidentLogger,
    HumanReviewQueue,
)

API_KEY = os.environ.get("RAIL_SCORE_API", "your-api-key-here")

# ---------------------------------------------------------------------------
# 1. Telemetry setup — console exporter (good for development)
# ---------------------------------------------------------------------------
print("=" * 60)
print("1. Telemetry Setup")
print("=" * 60)

telemetry = RAILTelemetry(
    org_id="acme-corp",
    project_id="customer-chatbot",
    environment="production",
    exporter="console",       # switch to "otlp" in production
    enable_traces=True,
    enable_metrics=True,
    enable_logs=True,
)
print(f"Telemetry ready — org={telemetry.org_id}, project={telemetry.project_id}")

# For production with an OTLP collector (Datadog, Grafana, etc.):
#
# telemetry = RAILTelemetry(
#     org_id="acme-corp",
#     project_id="customer-chatbot",
#     environment="production",
#     exporter="otlp",
#     endpoint="localhost:4317",          # your OTLP collector endpoint
#     protocol="grpc",                    # or "http"
#     headers={"Authorization": "Bearer <token>"},
# )

# ---------------------------------------------------------------------------
# 2. Multi-project scoping
#    Each RAILTelemetry instance is fully isolated — providers are not shared.
#    Spans and metrics carry rail.org_id + rail.project_id as first-class
#    attributes so you can filter per project in any OTEL backend.
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("2. Multi-Project Scoping")
print("=" * 60)

telemetry_search = RAILTelemetry(
    org_id="acme-corp",
    project_id="search-api",
    environment="production",
    exporter="console",
)

client_chatbot = RailScoreClient(api_key=API_KEY, telemetry=telemetry)
client_search  = RailScoreClient(api_key=API_KEY, telemetry=telemetry_search)

print("client_chatbot → traces tagged rail.project_id=customer-chatbot")
print("client_search  → traces tagged rail.project_id=search-api")
print("Every span, metric, and log is independently scoped per project.")

# ---------------------------------------------------------------------------
# 3. Auto-instrumented evaluation
#    Every call through a telemetry-enabled client emits:
#      - A span:   RAIL POST /railscore/v1/eval  (with score, confidence, mode)
#      - A metric: rail.requests counter, rail.request.duration histogram,
#                  rail.score.distribution histogram
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("3. Auto-Instrumented Evaluation")
print("=" * 60)

content = (
    "Regular exercise like walking 30 minutes daily improves cardiovascular "
    "health and reduces the risk of chronic diseases. Always consult your "
    "doctor before starting a new exercise program."
)

result = client_chatbot.eval(content=content, mode="basic")
print(f"RAIL Score:  {result.rail_score.score}/10")
print(f"Confidence:  {result.rail_score.confidence}")
print("→ Span emitted with rail.score, rail.confidence, rail.project_id=customer-chatbot")

# ---------------------------------------------------------------------------
# 4. ComplianceLogger — structured compliance logs per framework
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("4. ComplianceLogger")
print("=" * 60)

comp_logger = ComplianceLogger(telemetry)

compliance_content = (
    "Our AI system processes personal health records to make automated "
    "decisions about patient care. We collect medical history, genetic "
    "information, and behavioral patterns without explicit user consent."
)

gdpr_result = client_chatbot.compliance_check(
    content=compliance_content,
    framework="gdpr",
    context={"domain": "healthcare", "data_types": ["health_records", "genetic_data"]},
)

print(f"GDPR Score: {gdpr_result.compliance_score.score}/10 ({gdpr_result.compliance_score.label})")
comp_logger.log_compliance_result(gdpr_result)
print("→ Structured OTEL log emitted (INFO summary + WARNING/ERROR per issue)")

# Multi-framework logging
multi_result = client_chatbot.compliance_check(
    content=compliance_content,
    frameworks=["gdpr", "ccpa"],
)
comp_logger.log_multi_compliance_result(multi_result)
print("→ Cross-framework log emitted for gdpr + ccpa")

# ---------------------------------------------------------------------------
# 5. IncidentLogger — raise tracked incidents on threshold breaches
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("5. IncidentLogger")
print("=" * 60)

incident_logger = IncidentLogger(telemetry)

# Auto-raise from a compliance result that breached threshold
incident_id = incident_logger.log_compliance_incident(gdpr_result, threshold=6.0)
if incident_id:
    print(f"Compliance incident raised: {incident_id}")
    print(f"  → GDPR score {gdpr_result.compliance_score.score:.1f} breached threshold 6.0")

# Raise a score-breach incident manually
breach_id = incident_logger.log_score_breach(
    score=1.8,
    threshold=4.0,
    content_preview=compliance_content[:120],
    affected_dimensions=["privacy", "transparency"],
)
print(f"Score-breach incident raised: {breach_id}")

# Raise a fully custom incident
custom_id = incident_logger.log_incident(
    incident_type="policy_violation",
    severity="high",
    title="Sensitive PII detected in response",
    description="Response contained full name and address of a real individual.",
    affected_dimensions=["privacy"],
    metadata={"detected_by": "pii_scanner", "field": "response_text"},
)
print(f"Custom incident raised: {custom_id}")
print("→ All incidents carry rail.incident.id for correlation with external ticketing")

# ---------------------------------------------------------------------------
# 6. HumanReviewQueue — per-dimension queue for low-scoring content
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("6. HumanReviewQueue")
print("=" * 60)

review_queue = HumanReviewQueue(telemetry, threshold=2.0)

# Evaluate deep mode to get per-dimension scores with explanations
deep_result = client_chatbot.eval(
    content=(
        "Our AI tracks all users without consent and shares their data "
        "with third parties. We make fully automated decisions about credit "
        "scores with no human oversight or explanation."
    ),
    mode="deep",
    include_explanations=True,
    include_issues=True,
)

# Auto-check all 8 dimensions — enqueues anything scoring below 2.0
flagged = review_queue.check_and_enqueue(
    deep_result,
    content_preview=deep_result.explanation[:200] if deep_result.explanation else "",
    link_incident=True,   # also raise an IncidentLogger incident per flagged dimension
)

print(f"Flagged {len(flagged)} dimension(s) for human review:")
for item in flagged:
    print(f"  [{item.item_id}] {item.dimension}: score={item.score:.1f}  incident={item.incident_id}")

# Inspect queue without removing items
print(f"\nPending (all dimensions):       {review_queue.size()}")
print(f"Pending (privacy only):         {review_queue.size(dimension='privacy')}")
print(f"Pending (transparency only):    {review_queue.size(dimension='transparency')}")

# Manually enqueue a specific dimension
review_queue.enqueue(
    dimension="safety",
    score=1.5,
    content_preview="Contains instructions that could be misused.",
    explanation="Response describes techniques that pose a safety risk.",
)
print(f"\nAfter manual enqueue — safety queue: {review_queue.size(dimension='safety')}")

# Drain for forwarding to external system (Jira, PagerDuty, Slack, etc.)
all_items = review_queue.drain()
print(f"\nDrained {len(all_items)} item(s) for external handling:")
for item in all_items:
    print(f"  {item.dimension:20s}  score={item.score:.1f}  id={item.item_id}")
print("→ Each ReviewItem has item_id, dimension, score, explanation, issues, timestamp")
print("→ Integrate with your ticketing system: for item in review_queue.drain(): jira.create(item)")

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("Shutdown")
print("=" * 60)
telemetry.shutdown()
telemetry_search.shutdown()
print("All pending spans, metrics, and logs flushed.")
