"""RAIL Score SDK — OpenTelemetry integration.

Install with::

    pip install rail-score-sdk[telemetry]

Usage::

    from rail_score_sdk.telemetry import RAILTelemetry, ComplianceLogger
    from rail_score_sdk import RailScoreClient

    telemetry = RAILTelemetry(
        org_id="my-org",
        project_id="chatbot-v2",
        environment="production",
        exporter="console",
    )

    client = RailScoreClient(api_key="rail_xxx", telemetry=telemetry)
    result = client.eval("Some content", mode="basic")

    # Structured compliance logging
    comp_logger = ComplianceLogger(telemetry)
    comp_result = client.compliance_check("...", framework="gdpr")
    comp_logger.log_compliance_result(comp_result)

    telemetry.shutdown()
"""

from .core import RAILTelemetry
from .instrumentor import RAILInstrumentor
from .compliance_logger import ComplianceLogger, IncidentLogger
from . import constants

__all__ = [
    "RAILTelemetry",
    "RAILInstrumentor",
    "ComplianceLogger",
    "IncidentLogger",
    "constants",
]
