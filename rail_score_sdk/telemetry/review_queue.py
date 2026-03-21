"""Human review queue for low-scoring RAIL dimensions.

Any dimension that scores below the configured threshold (default 2.0) is
immediately enqueued for human review and emitted as a structured OTEL log
record so it appears in real-time in your observability backend.

Usage::

    from rail_score_sdk.telemetry import RAILTelemetry, HumanReviewQueue

    telemetry = RAILTelemetry(org_id="acme", project_id="chatbot-v2")
    review_queue = HumanReviewQueue(telemetry)

    result = client.eval(content, mode="deep")
    flagged = review_queue.check_and_enqueue(result, content_preview=content[:200])

    # Inspect pending items per dimension
    safety_items = review_queue.pending(dimension="safety")

    # Drain all items for external handling (e.g. push to Jira / PagerDuty)
    all_items = review_queue.drain()
"""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import constants as c
from .core import RAILTelemetry

try:
    from opentelemetry.sdk._logs import LogRecord
    from opentelemetry._logs import SeverityNumber

    _HAS_OTEL_LOGS = True
except ImportError:
    _HAS_OTEL_LOGS = False


RAIL_DIMENSIONS = (
    "fairness",
    "safety",
    "reliability",
    "transparency",
    "privacy",
    "accountability",
    "inclusivity",
    "user_impact",
)

DEFAULT_REVIEW_THRESHOLD = 2.0


@dataclass
class ReviewItem:
    """A single flagged dimension queued for human review.

    Attributes
    ----------
    item_id:
        Unique identifier for this review item (``rev_<12-char hex>``).
    dimension:
        The RAIL dimension that triggered the review (e.g. ``"safety"``).
    score:
        The dimension score that breached the threshold.
    threshold:
        The threshold that was configured when the item was enqueued.
    org_id:
        Organisation identifier from the telemetry configuration.
    project_id:
        Project identifier from the telemetry configuration.
    environment:
        Deployment environment from the telemetry configuration.
    timestamp:
        ISO-8601 UTC timestamp of when the item was enqueued.
    content_preview:
        First 200 characters of the evaluated content (empty if not provided).
    explanation:
        Per-dimension explanation from deep eval, if available.
    issues:
        Issue tags returned for this dimension, if available.
    incident_id:
        Linked incident ID if ``link_incident=True`` was passed to
        :meth:`check_and_enqueue`.
    metadata:
        Any extra key-value pairs passed at enqueue time.
    """

    item_id: str
    dimension: str
    score: float
    threshold: float
    org_id: str
    project_id: str
    environment: str
    timestamp: str
    content_preview: str = ""
    explanation: Optional[str] = None
    issues: Optional[List[str]] = None
    incident_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class HumanReviewQueue:
    """Per-project, per-dimension queue for flagging low RAIL scores.

    Items are enqueued when any dimension score falls below ``threshold``
    (default ``2.0``).  Each enqueue immediately emits a structured OTEL
    log record so the item appears in real-time in your observability backend.

    The in-memory queue lets you drain items at any point for further
    handling — e.g. pushing to Jira, PagerDuty, Slack, or a custom webhook.

    Parameters
    ----------
    telemetry : RAILTelemetry
        Telemetry instance that provides OTEL logger and project/org context.
    threshold : float
        Scores strictly below this value are flagged.  Default ``2.0``.

    Example::

        queue = HumanReviewQueue(telemetry, threshold=2.0)

        # Auto-check all 8 dimensions from an EvalResult
        flagged = queue.check_and_enqueue(eval_result, content_preview=text[:200])

        # Per-dimension inspection
        print(queue.pending(dimension="safety"))

        # Drain and forward to external system
        for item in queue.drain():
            my_ticketing_system.create(item)
    """

    def __init__(
        self,
        telemetry: RAILTelemetry,
        threshold: float = DEFAULT_REVIEW_THRESHOLD,
    ) -> None:
        self._telemetry = telemetry
        self.threshold = threshold
        self._queue: Dict[str, List[ReviewItem]] = defaultdict(list)
        self._otel_logger = telemetry.logger
        self._py_logger = logging.getLogger("rail.review_queue")

    # ------------------------------------------------------------------
    # Primary API
    # ------------------------------------------------------------------

    def check_and_enqueue(
        self,
        eval_result: Any,
        content_preview: str = "",
        threshold: Optional[float] = None,
        link_incident: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[ReviewItem]:
        """Inspect all 8 dimensions of ``eval_result`` and enqueue any that
        breach the threshold.

        Parameters
        ----------
        eval_result:
            An :class:`~rail_score_sdk.models.EvalResult` (or raw dict with a
            ``"dimension_scores"`` key).
        content_preview:
            Snippet of the evaluated content for context in the review item.
        threshold:
            Override the queue-level threshold for this call.
        link_incident:
            If ``True``, also raise an :class:`~rail_score_sdk.telemetry.IncidentLogger`
            incident for each flagged dimension and store the ``incident_id``
            on the review item.
        metadata:
            Extra key-value pairs attached to every review item from this call.

        Returns
        -------
        List[ReviewItem]
            The items that were enqueued (empty list if nothing was flagged).
        """
        effective_threshold = threshold if threshold is not None else self.threshold

        # Support both dataclass EvalResult and raw dict
        if hasattr(eval_result, "dimension_scores"):
            dim_scores = eval_result.dimension_scores  # Dict[str, DimensionScore]
        else:
            dim_scores = eval_result.get("dimension_scores", {})

        flagged: List[ReviewItem] = []

        for dim in RAIL_DIMENSIONS:
            ds = dim_scores.get(dim)
            if ds is None:
                continue

            score = ds.score if hasattr(ds, "score") else ds.get("score", 10.0)
            if score >= effective_threshold:
                continue

            explanation = (
                ds.explanation if hasattr(ds, "explanation") else ds.get("explanation")
            )
            issues = (
                ds.issues if hasattr(ds, "issues") else ds.get("issues")
            )

            incident_id: Optional[str] = None
            if link_incident:
                incident_id = self._raise_incident(
                    dimension=dim,
                    score=score,
                    threshold=effective_threshold,
                    content_preview=content_preview,
                )

            item = self.enqueue(
                dimension=dim,
                score=score,
                threshold=effective_threshold,
                content_preview=content_preview,
                explanation=explanation,
                issues=issues,
                incident_id=incident_id,
                metadata=metadata,
            )
            flagged.append(item)

        return flagged

    def enqueue(
        self,
        dimension: str,
        score: float,
        threshold: Optional[float] = None,
        content_preview: str = "",
        explanation: Optional[str] = None,
        issues: Optional[List[str]] = None,
        incident_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReviewItem:
        """Manually enqueue a single dimension for human review.

        Emits an OTEL log record immediately.  Returns the :class:`ReviewItem`.
        """
        effective_threshold = threshold if threshold is not None else self.threshold
        item = ReviewItem(
            item_id=f"rev_{uuid.uuid4().hex[:12]}",
            dimension=dimension,
            score=score,
            threshold=effective_threshold,
            org_id=self._telemetry.org_id,
            project_id=self._telemetry.project_id,
            environment=self._telemetry.environment,
            timestamp=datetime.now(timezone.utc).isoformat(),
            content_preview=content_preview[:200] if content_preview else "",
            explanation=explanation,
            issues=issues,
            incident_id=incident_id,
            metadata=metadata or {},
        )
        self._queue[dimension].append(item)
        self._emit_item(item)
        return item

    # ------------------------------------------------------------------
    # Queue inspection & drain
    # ------------------------------------------------------------------

    def pending(self, dimension: Optional[str] = None) -> List[ReviewItem]:
        """Return pending review items without removing them.

        Parameters
        ----------
        dimension:
            Filter to a specific dimension.  Returns all items if omitted.
        """
        if dimension:
            return list(self._queue.get(dimension, []))
        return [item for items in self._queue.values() for item in items]

    def drain(self, dimension: Optional[str] = None) -> List[ReviewItem]:
        """Remove and return all pending items (optionally filtered by dimension).

        Use this to forward items to an external system after inspecting them.
        """
        if dimension:
            items = list(self._queue.get(dimension, []))
            self._queue[dimension] = []
            return items

        all_items = self.pending()
        self._queue.clear()
        return all_items

    def size(self, dimension: Optional[str] = None) -> int:
        """Return the number of pending items (optionally per dimension)."""
        return len(self.pending(dimension))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _raise_incident(
        self,
        dimension: str,
        score: float,
        threshold: float,
        content_preview: str,
    ) -> str:
        """Raise an IncidentLogger incident and return the incident_id."""
        from .compliance_logger import IncidentLogger  # avoid circular import at module level

        incident_logger = IncidentLogger(self._telemetry)
        return incident_logger.log_incident(
            incident_type="score_breach",
            severity="critical" if score < threshold * 0.5 else "high",
            title=f"Concerning {dimension} score requires human review",
            description=(
                f"Dimension '{dimension}' scored {score:.1f}, below the "
                f"review threshold of {threshold:.1f}."
                + (f" Content: \"{content_preview[:120]}\"" if content_preview else "")
            ),
            score=score,
            threshold=threshold,
            affected_dimensions=[dimension],
        )

    def _emit_item(self, item: ReviewItem) -> None:
        """Emit the review item as a structured OTEL log record."""
        attrs: Dict[str, Any] = {
            "rail.review.item_id": item.item_id,
            "rail.review.dimension": item.dimension,
            "rail.review.score": item.score,
            "rail.review.threshold": item.threshold,
            "rail.review.status": "pending",
            c.RESOURCE_ORG_ID: item.org_id,
            c.RESOURCE_PROJECT_ID: item.project_id,
            c.RESOURCE_ENVIRONMENT: item.environment,
            "rail.review.timestamp": item.timestamp,
        }
        if item.content_preview:
            attrs["rail.review.content_preview"] = item.content_preview
        if item.explanation:
            attrs["rail.review.explanation"] = item.explanation
        if item.issues:
            attrs["rail.review.issues"] = ",".join(item.issues)
        if item.incident_id:
            attrs[c.ATTR_INCIDENT_ID] = item.incident_id
        for k, v in item.metadata.items():
            attrs[f"rail.review.meta.{k}"] = str(v)

        body = (
            f"[HUMAN REVIEW {item.item_id}] {item.dimension.upper()} score "
            f"{item.score:.1f} is below threshold {item.threshold:.1f} — "
            f"queued for human review. Project={item.project_id}"
        )

        if self._otel_logger is not None and _HAS_OTEL_LOGS:
            self._otel_logger.emit(
                LogRecord(
                    body=body,
                    severity_number=SeverityNumber.WARN,
                    severity_text="WARNING",
                    attributes=attrs,
                )
            )
        else:
            self._py_logger.warning(body, extra=attrs)
