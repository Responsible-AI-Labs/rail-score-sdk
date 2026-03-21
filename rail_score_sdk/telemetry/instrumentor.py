"""Monkey-patch instrumentor for sync and async RAIL clients."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from . import constants as c
from .core import RAILTelemetry

try:
    from opentelemetry import trace
    from opentelemetry.trace import StatusCode

    _HAS_OTEL = True
except ImportError:
    _HAS_OTEL = False


class RAILInstrumentor:
    """Wraps RAIL client ``_request`` methods with OTEL spans and metrics.

    Usage::

        telem = RAILTelemetry(org_id="acme", project_id="chatbot")
        instrumentor = RAILInstrumentor(telem)
        instrumentor.instrument_sync_client(client)
    """

    def __init__(self, telemetry: RAILTelemetry) -> None:
        self._telemetry = telemetry
        self._tracer = telemetry.tracer
        self._meter = telemetry.meter
        self._org_id = telemetry.org_id
        self._project_id = telemetry.project_id

        # Create metric instruments
        self._request_counter = self._meter.create_counter(
            name=c.METRIC_REQUESTS,
            description="Total RAIL API requests",
            unit="1",
        )
        self._duration_histogram = self._meter.create_histogram(
            name=c.METRIC_REQUEST_DURATION,
            description="RAIL API request duration",
            unit="ms",
        )
        self._error_counter = self._meter.create_counter(
            name=c.METRIC_ERRORS,
            description="Total RAIL API errors",
            unit="1",
        )
        self._score_histogram = self._meter.create_histogram(
            name=c.METRIC_SCORE_DISTRIBUTION,
            description="Distribution of RAIL scores",
            unit="1",
        )
        self._credits_counter = self._meter.create_counter(
            name=c.METRIC_CREDITS_CONSUMED,
            description="Total RAIL credits consumed",
            unit="1",
        )

    # ------------------------------------------------------------------
    # Sync client instrumentation
    # ------------------------------------------------------------------
    def instrument_sync_client(self, client: Any) -> None:
        """Wrap the sync client's ``_request`` method."""
        original_request = client._request

        def instrumented_request(
            method: str,
            endpoint: str,
            json: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            authenticated: bool = True,
        ) -> Dict[str, Any]:
            span_name = f"RAIL {method} {endpoint}"
            with self._tracer.start_as_current_span(span_name) as span:
                span.set_attribute(c.ATTR_ENDPOINT, endpoint)
                span.set_attribute(c.RESOURCE_ORG_ID, self._org_id)
                span.set_attribute(c.RESOURCE_PROJECT_ID, self._project_id)
                if json:
                    if "mode" in json:
                        span.set_attribute(c.ATTR_MODE, json["mode"])
                    if "domain" in json:
                        span.set_attribute(c.ATTR_DOMAIN, json["domain"])

                attrs = {"endpoint": endpoint, "rail.org_id": self._org_id, "rail.project_id": self._project_id}
                self._request_counter.add(1, attrs)
                start = time.monotonic()

                try:
                    result = original_request(
                        method, endpoint, json=json, params=params,
                        authenticated=authenticated,
                    )
                    duration_ms = (time.monotonic() - start) * 1000
                    self._duration_histogram.record(duration_ms, attrs)

                    self._enrich_span(span, endpoint, result, json)
                    return result

                except Exception as exc:
                    duration_ms = (time.monotonic() - start) * 1000
                    self._duration_histogram.record(duration_ms, attrs)
                    self._error_counter.add(1, attrs)
                    if _HAS_OTEL:
                        span.set_status(StatusCode.ERROR, str(exc))
                        span.record_exception(exc)
                    raise

        client._request = instrumented_request

    # ------------------------------------------------------------------
    # Async client instrumentation
    # ------------------------------------------------------------------
    def instrument_async_client(self, client: Any) -> None:
        """Wrap the async client's ``_request`` method."""
        original_request = client._request

        async def instrumented_request(
            method: str,
            path: str,
            payload: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            span_name = f"RAIL {method} {path}"
            with self._tracer.start_as_current_span(span_name) as span:
                span.set_attribute(c.ATTR_ENDPOINT, path)
                span.set_attribute(c.RESOURCE_ORG_ID, self._org_id)
                span.set_attribute(c.RESOURCE_PROJECT_ID, self._project_id)
                if payload:
                    if "mode" in payload:
                        span.set_attribute(c.ATTR_MODE, payload["mode"])
                    if "domain" in payload:
                        span.set_attribute(c.ATTR_DOMAIN, payload["domain"])

                attrs = {"endpoint": path, "rail.org_id": self._org_id, "rail.project_id": self._project_id}
                self._request_counter.add(1, attrs)
                start = time.monotonic()

                try:
                    result = await original_request(method, path, payload)
                    duration_ms = (time.monotonic() - start) * 1000
                    self._duration_histogram.record(duration_ms, attrs)

                    self._enrich_span(span, path, result, payload)
                    return result

                except Exception as exc:
                    duration_ms = (time.monotonic() - start) * 1000
                    self._duration_histogram.record(duration_ms, attrs)
                    self._error_counter.add(1, attrs)
                    if _HAS_OTEL:
                        span.set_status(StatusCode.ERROR, str(exc))
                        span.record_exception(exc)
                    raise

        client._request = instrumented_request

    # ------------------------------------------------------------------
    # Post-call enrichment
    # ------------------------------------------------------------------
    def _enrich_span(
        self,
        span: Any,
        endpoint: str,
        data: Dict[str, Any],
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add result-specific attributes to the span and record metrics."""

        # Eval endpoint enrichment
        if "/eval" in endpoint:
            result = data.get("result", data)
            rail_score = result.get("rail_score", {})
            score = rail_score.get("score")
            confidence = rail_score.get("confidence")
            if score is not None:
                span.set_attribute(c.ATTR_SCORE, score)
                self._score_histogram.record(score, {"endpoint": endpoint})
            if confidence is not None:
                span.set_attribute(c.ATTR_CONFIDENCE, confidence)
            from_cache = result.get("from_cache", False)
            span.set_attribute(c.ATTR_FROM_CACHE, from_cache)

        # Safe-regenerate endpoint enrichment
        elif "/safe-regenerate" in endpoint:
            result_obj = data.get("result", data)
            status = result_obj.get("status")
            if status:
                span.set_attribute(c.ATTR_REGEN_STATUS, status)
            if payload and "regeneration_model" in payload:
                span.set_attribute(c.ATTR_REGEN_MODEL, payload["regeneration_model"])
            history = result_obj.get("iteration_history", [])
            span.set_attribute(c.ATTR_REGEN_ITERATIONS, len(history))
            credits = data.get("credits_consumed", 0)
            if credits:
                span.set_attribute(c.ATTR_CREDITS_CONSUMED, credits)
                self._credits_counter.add(credits, {"endpoint": endpoint})

        # Compliance endpoint enrichment
        elif "/compliance" in endpoint:
            # Single framework
            result = data.get("result", {})
            if isinstance(result, dict) and "compliance_score" in result:
                cs = result["compliance_score"]
                span.set_attribute(c.ATTR_COMPLIANCE_FRAMEWORK, result.get("framework", ""))
                span.set_attribute(c.ATTR_COMPLIANCE_SCORE, cs.get("score", 0))
                span.set_attribute(c.ATTR_COMPLIANCE_LABEL, cs.get("label", ""))
                span.set_attribute(
                    c.ATTR_COMPLIANCE_REQS_PASSED, result.get("requirements_passed", 0)
                )
                span.set_attribute(
                    c.ATTR_COMPLIANCE_REQS_FAILED, result.get("requirements_failed", 0)
                )
            # Multi-framework
            if "results" in data:
                frameworks = list(data["results"].keys())
                span.set_attribute(c.ATTR_COMPLIANCE_FRAMEWORK, ",".join(frameworks))
