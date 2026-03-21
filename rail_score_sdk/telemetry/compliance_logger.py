"""Structured OTEL logging for compliance check results."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from . import constants as c
from .core import RAILTelemetry

try:
    from opentelemetry.sdk._logs import LoggerProvider, LogRecord
    from opentelemetry._logs import SeverityNumber

    _HAS_OTEL_LOGS = True
except ImportError:
    _HAS_OTEL_LOGS = False


class ComplianceLogger:
    """Emit structured OTEL log records for compliance results.

    Falls back to Python ``logging`` if OTEL log SDK is unavailable.

    Parameters
    ----------
    telemetry : RAILTelemetry
        The telemetry instance (provides logger + resource attributes).
    """

    def __init__(self, telemetry: RAILTelemetry) -> None:
        self._telemetry = telemetry
        self._otel_logger = telemetry.logger
        self._py_logger = logging.getLogger("rail.compliance")

    def log_compliance_result(
        self,
        result: Any,
        content_preview: str = "",
    ) -> None:
        """Log a single-framework :class:`ComplianceResult`.

        Emits:
        - INFO: summary (framework, score, label, requirements)
        - WARNING: per-issue for failed requirements
        - ERROR: critical violations (severity ``high``)
        """
        # Handle both dataclass and dict results
        if hasattr(result, "framework"):
            framework = result.framework
            score = result.compliance_score.score
            label = result.compliance_score.label
            summary = result.compliance_score.summary
            reqs_passed = result.requirements_passed
            reqs_failed = result.requirements_failed
            issues = result.issues
        else:
            framework = result.get("framework", "unknown")
            cs = result.get("compliance_score", {})
            score = cs.get("score", 0)
            label = cs.get("label", "unknown")
            summary = cs.get("summary", "")
            reqs_passed = result.get("requirements_passed", 0)
            reqs_failed = result.get("requirements_failed", 0)
            issues = result.get("issues", [])

        attrs = {
            c.ATTR_COMPLIANCE_FRAMEWORK: framework,
            c.ATTR_COMPLIANCE_SCORE: score,
            c.ATTR_COMPLIANCE_LABEL: label,
            c.ATTR_COMPLIANCE_REQS_PASSED: reqs_passed,
            c.ATTR_COMPLIANCE_REQS_FAILED: reqs_failed,
            c.RESOURCE_ORG_ID: self._telemetry.org_id,
            c.RESOURCE_PROJECT_ID: self._telemetry.project_id,
            c.RESOURCE_ENVIRONMENT: self._telemetry.environment,
        }

        # Summary log (INFO)
        self._emit(
            level="INFO",
            body=(
                f"Compliance check: {framework} → {label} "
                f"(score={score:.1f}, passed={reqs_passed}, failed={reqs_failed}). "
                f"{summary}"
            ),
            attributes=attrs,
        )

        # Per-issue logs
        for issue in issues:
            if hasattr(issue, "id"):
                issue_id = issue.id
                desc = issue.description
                dim = issue.dimension
                severity = issue.severity
                article = issue.article
                remediation = issue.remediation_effort
            else:
                issue_id = issue.get("id", "")
                desc = issue.get("description", "")
                dim = issue.get("dimension", "")
                severity = issue.get("severity", "low")
                article = issue.get("article", "")
                remediation = issue.get("remediation_effort", "")

            issue_attrs = {
                **attrs,
                "issue.id": issue_id,
                "issue.dimension": dim,
                "issue.severity": severity,
                "issue.article": article,
                "issue.remediation_effort": remediation,
            }

            level = "ERROR" if severity == "high" else "WARNING"
            self._emit(
                level=level,
                body=f"[{framework}] {severity.upper()} issue ({issue_id}): {desc}",
                attributes=issue_attrs,
            )

    def log_multi_compliance_result(
        self,
        result: Any,
    ) -> None:
        """Log a :class:`MultiComplianceResult` across multiple frameworks."""
        if hasattr(result, "results"):
            results_dict = result.results
            summary = result.cross_framework_summary
        else:
            results_dict = result.get("results", {})
            summary = result.get("cross_framework_summary", {})

        # Log cross-framework summary
        if hasattr(summary, "average_score"):
            avg = summary.average_score
            weakest = summary.weakest_framework
            weakest_score = summary.weakest_score
            n_frameworks = summary.frameworks_evaluated
        else:
            avg = summary.get("average_score", 0)
            weakest = summary.get("weakest_framework", "")
            weakest_score = summary.get("weakest_score", 0)
            n_frameworks = summary.get("frameworks_evaluated", 0)

        self._emit(
            level="INFO",
            body=(
                f"Multi-compliance: {n_frameworks} frameworks evaluated. "
                f"Average={avg:.1f}, weakest={weakest} ({weakest_score:.1f})"
            ),
            attributes={
                c.RESOURCE_ORG_ID: self._telemetry.org_id,
                c.RESOURCE_PROJECT_ID: self._telemetry.project_id,
                c.RESOURCE_ENVIRONMENT: self._telemetry.environment,
            },
        )

        # Log each framework individually
        for fw_key, fw_result in results_dict.items():
            self.log_compliance_result(fw_result)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _emit(
        self,
        level: str,
        body: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit via OTEL logger if available, otherwise Python logging."""
        if self._otel_logger is not None and _HAS_OTEL_LOGS:
            severity_map = {
                "DEBUG": SeverityNumber.DEBUG,
                "INFO": SeverityNumber.INFO,
                "WARNING": SeverityNumber.WARN,
                "ERROR": SeverityNumber.ERROR,
            }
            self._otel_logger.emit(
                LogRecord(
                    body=body,
                    severity_number=severity_map.get(level, SeverityNumber.INFO),
                    severity_text=level,
                    attributes=attributes or {},
                )
            )
        else:
            py_level = getattr(logging, level, logging.INFO)
            self._py_logger.log(py_level, body, extra=attributes or {})
