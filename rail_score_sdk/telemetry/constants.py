"""Semantic attribute names and metric instrument names for RAIL telemetry."""

# ---------------------------------------------------------------------------
# Resource attributes (set once at init)
# ---------------------------------------------------------------------------
RESOURCE_ORG_ID = "rail.org_id"
RESOURCE_PROJECT_ID = "rail.project_id"
RESOURCE_ENVIRONMENT = "rail.environment"
RESOURCE_SDK_VERSION = "rail.sdk.version"

# ---------------------------------------------------------------------------
# Span attributes (set per-request)
# ---------------------------------------------------------------------------
ATTR_ENDPOINT = "rail.endpoint"
ATTR_MODE = "rail.mode"
ATTR_DOMAIN = "rail.domain"
ATTR_SCORE = "rail.score"
ATTR_CONFIDENCE = "rail.confidence"
ATTR_CREDITS_CONSUMED = "rail.credits_consumed"
ATTR_FROM_CACHE = "rail.from_cache"

# Safe-regenerate attributes
ATTR_REGEN_STATUS = "rail.regenerate.status"
ATTR_REGEN_MODEL = "rail.regenerate.model"
ATTR_REGEN_ITERATIONS = "rail.regenerate.iterations"

# Compliance attributes
ATTR_COMPLIANCE_FRAMEWORK = "rail.compliance.framework"
ATTR_COMPLIANCE_SCORE = "rail.compliance.score"
ATTR_COMPLIANCE_LABEL = "rail.compliance.label"
ATTR_COMPLIANCE_REQS_PASSED = "rail.compliance.requirements_passed"
ATTR_COMPLIANCE_REQS_FAILED = "rail.compliance.requirements_failed"

# Incident attributes
ATTR_INCIDENT_ID = "rail.incident.id"
ATTR_INCIDENT_TYPE = "rail.incident.type"
ATTR_INCIDENT_SEVERITY = "rail.incident.severity"
ATTR_INCIDENT_STATUS = "rail.incident.status"
ATTR_INCIDENT_TITLE = "rail.incident.title"
ATTR_INCIDENT_THRESHOLD = "rail.incident.threshold"
ATTR_INCIDENT_AFFECTED_DIMS = "rail.incident.affected_dimensions"

# ---------------------------------------------------------------------------
# Metric instrument names
# ---------------------------------------------------------------------------
METRIC_REQUESTS = "rail.requests"
METRIC_REQUEST_DURATION = "rail.request.duration"
METRIC_ERRORS = "rail.errors"
METRIC_SCORE_DISTRIBUTION = "rail.score.distribution"
METRIC_CREDITS_CONSUMED = "rail.credits.consumed"
