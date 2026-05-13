"""Structured OTEL logging for compliance check results and incidents."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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

    def log_dpdp_content_result(
        self,
        result: Any,
        content_preview: str = "",
    ) -> None:
        """Log a DPDP content scan result.

        Emits INFO for clean scans, WARNING for PII detections,
        and ERROR for violations with block actions.
        """
        compliant = getattr(result, "compliant", True)
        pii_found = getattr(result, "pii_found", [])
        violations = getattr(result, "violations", [])
        child_signals = getattr(result, "child_signals", [])

        attrs = {
            c.ATTR_DPDP_PII_COUNT: len(pii_found),
            c.ATTR_DPDP_CHILD_DETECTED: len(child_signals) > 0,
            c.RESOURCE_ORG_ID: self._telemetry.org_id,
            c.RESOURCE_PROJECT_ID: self._telemetry.project_id,
            c.RESOURCE_ENVIRONMENT: self._telemetry.environment,
        }

        if compliant and not violations:
            self._emit(
                level="INFO",
                body=(
                    f"DPDP content scan: compliant "
                    f"(pii={len(pii_found)}, child_signals={len(child_signals)})"
                ),
                attributes=attrs,
            )
        else:
            for v in violations:
                v_attrs = {
                    **attrs,
                    c.ATTR_DPDP_VIOLATION_TYPE: v.check,
                    c.ATTR_DPDP_SECTION: v.section,
                    c.ATTR_DPDP_ACTION: v.action,
                }
                level = "ERROR" if v.action == "block" else "WARNING"
                self._emit(
                    level=level,
                    body=f"[DPDP {v.section}] {v.check}: {v.reason}",
                    attributes=v_attrs,
                )

    def log_dpdp_violation(
        self,
        violation: Any,
    ) -> None:
        """Log a single DPDP violation."""
        attrs = {
            c.ATTR_DPDP_VIOLATION_TYPE: violation.check,
            c.ATTR_DPDP_SECTION: violation.section,
            c.ATTR_DPDP_ACTION: violation.action,
            c.RESOURCE_ORG_ID: self._telemetry.org_id,
            c.RESOURCE_PROJECT_ID: self._telemetry.project_id,
            c.RESOURCE_ENVIRONMENT: self._telemetry.environment,
        }
        level = "ERROR" if violation.action == "block" else "WARNING"
        self._emit(
            level=level,
            body=f"[DPDP {violation.section}] {violation.check}: {violation.reason}",
            attributes=attrs,
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


class IncidentLogger:
    """Emit structured OTEL log records for compliance and score incidents.

    An incident is raised when a compliance check or RAIL score breaches a
    threshold that warrants tracking, alerting, or escalation.  Each incident
    gets a unique ``incident_id`` so it can be correlated across logs, traces,
    and external ticketing systems.

    Parameters
    ----------
    telemetry : RAILTelemetry
        The telemetry instance (provides logger + project/org attributes).

    Example::

        incident_logger = IncidentLogger(telemetry)

        # Auto-raise from a compliance result that breached threshold
        incident_logger.log_compliance_incident(gdpr_result, threshold=6.0)

        # Manually raise a score-breach incident
        incident_logger.log_score_breach(score=3.2, threshold=6.0)

        # Raise a custom incident
        incident_logger.log_incident(
            incident_type="policy_violation",
            severity="high",
            title="GDPR data minimisation breach",
            description="Response exposes unnecessary PII fields.",
        )
    """

    def __init__(self, telemetry: "RAILTelemetry") -> None:  # noqa: F821
        self._telemetry = telemetry
        self._otel_logger = telemetry.logger
        self._py_logger = logging.getLogger("rail.incident")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_incident(
        self,
        incident_type: str,
        severity: str,
        title: str,
        description: str,
        framework: str = "",
        score: Optional[float] = None,
        threshold: Optional[float] = None,
        affected_dimensions: Optional[List[str]] = None,
        incident_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Emit a structured incident log record and return the incident_id.

        Parameters
        ----------
        incident_type:
            Category of the incident — e.g. ``"compliance_violation"``,
            ``"score_breach"``, ``"policy_violation"``.
        severity:
            ``"critical"`` | ``"high"`` | ``"medium"`` | ``"low"``
        title:
            Short human-readable title for the incident.
        description:
            Full description of what triggered the incident.
        framework:
            Compliance framework involved (e.g. ``"gdpr"``), if applicable.
        score:
            The actual score that triggered the incident.
        threshold:
            The threshold that was breached.
        affected_dimensions:
            RAIL dimensions involved (e.g. ``["privacy", "transparency"]``).
        incident_id:
            Supply your own ID for correlation; auto-generated if omitted.
        metadata:
            Any extra key-value pairs to attach to the log record.
        """
        incident_id = incident_id or f"inc_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        attrs: Dict[str, Any] = {
            c.ATTR_INCIDENT_ID: incident_id,
            c.ATTR_INCIDENT_TYPE: incident_type,
            c.ATTR_INCIDENT_SEVERITY: severity,
            c.ATTR_INCIDENT_STATUS: "open",
            c.ATTR_INCIDENT_TITLE: title,
            c.RESOURCE_ORG_ID: self._telemetry.org_id,
            c.RESOURCE_PROJECT_ID: self._telemetry.project_id,
            c.RESOURCE_ENVIRONMENT: self._telemetry.environment,
            "rail.incident.timestamp": timestamp,
        }

        if framework:
            attrs[c.ATTR_COMPLIANCE_FRAMEWORK] = framework
        if score is not None:
            attrs[c.ATTR_INCIDENT_THRESHOLD] = threshold or 0.0
            attrs[c.ATTR_COMPLIANCE_SCORE] = score
        if threshold is not None:
            attrs[c.ATTR_INCIDENT_THRESHOLD] = threshold
        if affected_dimensions:
            attrs[c.ATTR_INCIDENT_AFFECTED_DIMS] = ",".join(affected_dimensions)
        if metadata:
            for k, v in metadata.items():
                attrs[f"rail.incident.meta.{k}"] = str(v)

        level = (
            "CRITICAL"
            if severity == "critical"
            else "ERROR" if severity == "high" else "WARNING"
        )
        self._emit(
            level=level,
            body=(
                f"[INCIDENT {incident_id}] {severity.upper()} {incident_type}: {title}. "
                f"{description}"
            ),
            attributes=attrs,
        )
        return incident_id

    def log_compliance_incident(
        self,
        result: Any,
        threshold: float = 5.0,
        incident_id: Optional[str] = None,
    ) -> Optional[str]:
        """Raise an incident if a compliance result score is below ``threshold``.

        Returns the ``incident_id`` if an incident was raised, else ``None``.
        """
        if hasattr(result, "compliance_score"):
            framework = result.framework
            score = result.compliance_score.score
            label = result.compliance_score.label
            issues = result.issues or []
        else:
            framework = result.get("framework", "unknown")
            cs = result.get("compliance_score", {})
            score = cs.get("score", 0)
            label = cs.get("label", "unknown")
            issues = result.get("issues", [])

        if score >= threshold:
            return None

        high_issues = [
            i
            for i in issues
            if (i.severity if hasattr(i, "severity") else i.get("severity", ""))
            == "high"
        ]
        severity = "critical" if score < threshold * 0.5 else "high"
        affected_dims = list(
            {
                (i.dimension if hasattr(i, "dimension") else i.get("dimension", ""))
                for i in issues
                if (i.dimension if hasattr(i, "dimension") else i.get("dimension", ""))
            }
        )

        return self.log_incident(
            incident_type="compliance_violation",
            severity=severity,
            title=f"{framework.upper()} compliance score below threshold",
            description=(
                f"Score {score:.1f} breached threshold {threshold:.1f} "
                f"(label={label}, high-severity issues={len(high_issues)})."
            ),
            framework=framework,
            score=score,
            threshold=threshold,
            affected_dimensions=affected_dims,
            incident_id=incident_id,
        )

    def log_score_breach(
        self,
        score: float,
        threshold: float,
        content_preview: str = "",
        affected_dimensions: Optional[List[str]] = None,
        incident_id: Optional[str] = None,
    ) -> str:
        """Raise an incident when a RAIL score drops below ``threshold``."""
        severity = "critical" if score < threshold * 0.5 else "high"
        description = f"RAIL score {score:.1f} is below threshold {threshold:.1f}."
        if content_preview:
            description += f' Content preview: "{content_preview[:120]}"'

        return self.log_incident(
            incident_type="score_breach",
            severity=severity,
            title=f"RAIL score breach (score={score:.1f}, threshold={threshold:.1f})",
            description=description,
            score=score,
            threshold=threshold,
            affected_dimensions=affected_dimensions,
            incident_id=incident_id,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _emit(
        self,
        level: str,
        body: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self._otel_logger is not None and _HAS_OTEL_LOGS:
            severity_map = {
                "DEBUG": SeverityNumber.DEBUG,
                "INFO": SeverityNumber.INFO,
                "WARNING": SeverityNumber.WARN,
                "ERROR": SeverityNumber.ERROR,
                "CRITICAL": SeverityNumber.FATAL,
            }
            self._otel_logger.emit(
                LogRecord(
                    body=body,
                    severity_number=severity_map.get(level, SeverityNumber.ERROR),
                    severity_text=level,
                    attributes=attributes or {},
                )
            )
        else:
            py_level = getattr(logging, level, logging.ERROR)
            self._py_logger.log(py_level, body, extra=attributes or {})
