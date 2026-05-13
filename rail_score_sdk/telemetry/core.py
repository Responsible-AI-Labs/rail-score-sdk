"""Core telemetry configuration — builds OTEL providers and exporters."""

from __future__ import annotations

from typing import Any, Dict, Optional

from . import constants as c

try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )

    _HAS_OTEL_SDK = True
except ImportError:
    _HAS_OTEL_SDK = False

try:
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import (
        BatchLogRecordProcessor,
        ConsoleLogExporter,
    )

    _HAS_OTEL_LOGS = True
except ImportError:
    _HAS_OTEL_LOGS = False

try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter as OTLPSpanExporterGRPC,
    )
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
        OTLPMetricExporter as OTLPMetricExporterGRPC,
    )

    _HAS_OTLP_GRPC = True
except ImportError:
    _HAS_OTLP_GRPC = False

try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter as OTLPSpanExporterHTTP,
    )
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
        OTLPMetricExporter as OTLPMetricExporterHTTP,
    )

    _HAS_OTLP_HTTP = True
except ImportError:
    _HAS_OTLP_HTTP = False

try:
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
        OTLPLogExporter as OTLPLogExporterGRPC,
    )

    _HAS_OTLP_LOG_GRPC = True
except ImportError:
    _HAS_OTLP_LOG_GRPC = False

try:
    from opentelemetry.exporter.otlp.proto.http._log_exporter import (
        OTLPLogExporter as OTLPLogExporterHTTP,
    )

    _HAS_OTLP_LOG_HTTP = True
except ImportError:
    _HAS_OTLP_LOG_HTTP = False


def _require_otel_sdk() -> None:
    if not _HAS_OTEL_SDK:
        raise ImportError(
            "OpenTelemetry SDK is required for RAIL telemetry. "
            "Install it with: pip install rail-score-sdk[telemetry]"
        )


class RAILTelemetry:
    """Vendor-neutral observability for the RAIL Score SDK.

    Parameters
    ----------
    org_id : str
        Organisation identifier for resource grouping.
    project_id : str
        Project identifier for resource grouping.
    environment : str
        Deployment environment (e.g. ``"production"``, ``"staging"``).
    service_name : str
        OTEL service name (default ``"rail-score-sdk"``).
    exporter : str
        ``"otlp"`` | ``"console"`` | ``"none"``.
    endpoint : str
        OTLP collector endpoint (only for ``exporter="otlp"``).
    protocol : str
        ``"grpc"`` or ``"http"`` (only for ``exporter="otlp"``).
    headers : dict
        Extra headers for the OTLP exporter (e.g. API keys).
    log_level : str
        Minimum log level for the OTEL logger (default ``"INFO"``).
    enable_traces : bool
        Enable distributed tracing (default ``True``).
    enable_metrics : bool
        Enable metrics collection (default ``True``).
    enable_logs : bool
        Enable structured logging (default ``True``).
    """

    def __init__(
        self,
        org_id: str = "",
        project_id: str = "",
        environment: str = "development",
        service_name: str = "rail-score-sdk",
        exporter: str = "console",
        endpoint: str = "localhost:4317",
        protocol: str = "grpc",
        headers: Optional[Dict[str, str]] = None,
        log_level: str = "INFO",
        enable_traces: bool = True,
        enable_metrics: bool = True,
        enable_logs: bool = True,
    ) -> None:
        _require_otel_sdk()

        self.org_id = org_id
        self.project_id = project_id
        self.environment = environment
        self.exporter = exporter
        self.endpoint = endpoint
        self.protocol = protocol
        self.headers = headers or {}
        self.log_level = log_level
        self.enable_traces = enable_traces
        self.enable_metrics = enable_metrics
        self.enable_logs = enable_logs

        # Import version lazily to avoid circular imports
        try:
            from rail_score_sdk import __version__
        except ImportError:
            __version__ = "unknown"

        self._resource = Resource.create(
            {
                "service.name": service_name,
                c.RESOURCE_ORG_ID: org_id,
                c.RESOURCE_PROJECT_ID: project_id,
                c.RESOURCE_ENVIRONMENT: environment,
                c.RESOURCE_SDK_VERSION: __version__,
            }
        )

        self._tracer_provider: Optional[Any] = None
        self._meter_provider: Optional[Any] = None
        self._logger_provider: Optional[Any] = None

        if enable_traces:
            self._setup_traces()
        if enable_metrics:
            self._setup_metrics()
        if enable_logs:
            self._setup_logs()

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------
    def _setup_traces(self) -> None:
        if self.exporter == "none":
            return
        tp = TracerProvider(resource=self._resource)
        if self.exporter == "console":
            tp.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        elif self.exporter == "otlp":
            span_exporter = self._create_otlp_span_exporter()
            tp.add_span_processor(BatchSpanProcessor(span_exporter))
        self._tracer_provider = tp

    def _setup_metrics(self) -> None:
        if self.exporter == "none":
            return
        if self.exporter == "console":
            reader = PeriodicExportingMetricReader(
                ConsoleMetricExporter(), export_interval_millis=10000
            )
        elif self.exporter == "otlp":
            metric_exporter = self._create_otlp_metric_exporter()
            reader = PeriodicExportingMetricReader(metric_exporter)
        else:
            return
        self._meter_provider = MeterProvider(
            resource=self._resource, metric_readers=[reader]
        )

    def _setup_logs(self) -> None:
        if self.exporter == "none":
            return
        if not _HAS_OTEL_LOGS:
            return
        lp = LoggerProvider(resource=self._resource)
        if self.exporter == "console":
            lp.add_log_record_processor(BatchLogRecordProcessor(ConsoleLogExporter()))
        elif self.exporter == "otlp":
            log_exporter = self._create_otlp_log_exporter()
            if log_exporter is not None:
                lp.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        self._logger_provider = lp

    # ------------------------------------------------------------------
    # OTLP exporter factories
    # ------------------------------------------------------------------
    def _create_otlp_span_exporter(self) -> Any:
        if self.protocol == "grpc":
            if not _HAS_OTLP_GRPC:
                raise ImportError(
                    "opentelemetry-exporter-otlp-proto-grpc is required for gRPC export."
                )
            return OTLPSpanExporterGRPC(endpoint=self.endpoint, headers=self.headers)
        if not _HAS_OTLP_HTTP:
            raise ImportError(
                "opentelemetry-exporter-otlp-proto-http is required for HTTP export."
            )
        return OTLPSpanExporterHTTP(endpoint=self.endpoint, headers=self.headers)

    def _create_otlp_metric_exporter(self) -> Any:
        if self.protocol == "grpc":
            if not _HAS_OTLP_GRPC:
                raise ImportError(
                    "opentelemetry-exporter-otlp-proto-grpc is required for gRPC export."
                )
            return OTLPMetricExporterGRPC(endpoint=self.endpoint, headers=self.headers)
        if not _HAS_OTLP_HTTP:
            raise ImportError(
                "opentelemetry-exporter-otlp-proto-http is required for HTTP export."
            )
        return OTLPMetricExporterHTTP(endpoint=self.endpoint, headers=self.headers)

    def _create_otlp_log_exporter(self) -> Any:
        if self.protocol == "grpc" and _HAS_OTLP_LOG_GRPC:
            return OTLPLogExporterGRPC(endpoint=self.endpoint, headers=self.headers)
        if self.protocol == "http" and _HAS_OTLP_LOG_HTTP:
            return OTLPLogExporterHTTP(endpoint=self.endpoint, headers=self.headers)
        return None

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------
    @property
    def tracer(self) -> Any:
        """Return a ``Tracer`` for creating spans."""
        if self._tracer_provider is None:
            return trace.get_tracer("rail-score-sdk")
        return self._tracer_provider.get_tracer("rail-score-sdk")

    @property
    def meter(self) -> Any:
        """Return a ``Meter`` for creating metrics."""
        if self._meter_provider is None:
            return metrics.get_meter("rail-score-sdk")
        return self._meter_provider.get_meter("rail-score-sdk")

    @property
    def logger(self) -> Any:
        """Return an OTEL ``Logger`` for structured log records."""
        if self._logger_provider is None:
            return None
        return self._logger_provider.get_logger("rail-score-sdk")

    @property
    def resource(self) -> Any:
        """The OTEL ``Resource`` with org/project/env attributes."""
        return self._resource

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def shutdown(self) -> None:
        """Flush pending telemetry data and release resources."""
        if self._tracer_provider is not None:
            self._tracer_provider.shutdown()
        if self._meter_provider is not None:
            self._meter_provider.shutdown()
        if self._logger_provider is not None:
            self._logger_provider.shutdown()
