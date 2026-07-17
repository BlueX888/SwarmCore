from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.metrics import Counter, Histogram, Meter, UpDownCounter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Tracer


@dataclass(frozen=True)
class Telemetry:
    tracer_provider: TracerProvider | None
    meter_provider: MeterProvider | None

    def shutdown(self) -> None:
        if self.meter_provider is not None:
            self.meter_provider.shutdown()
        if self.tracer_provider is not None:
            self.tracer_provider.shutdown()


def configure_telemetry(
    service_name: str,
    *,
    endpoint: str | None = None,
    enabled: bool = True,
) -> Telemetry:
    """Configure OTLP once for a process; Phoenix accepts the emitted OTLP data."""
    if not enabled:
        return Telemetry(None, None)
    resource = Resource.create({"service.name": service_name, "service.namespace": "swarmcore"})
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[
            PeriodicExportingMetricReader(
                OTLPMetricExporter(endpoint=endpoint, insecure=True),
                export_interval_millis=30_000,
            )
        ],
    )
    trace.set_tracer_provider(tracer_provider)
    metrics.set_meter_provider(meter_provider)
    return Telemetry(tracer_provider, meter_provider)


def get_tracer(component: str) -> Tracer:
    return trace.get_tracer(f"swarmcore.{component}")


def get_meter(component: str) -> Meter:
    return metrics.get_meter(f"swarmcore.{component}")


@dataclass(frozen=True)
class SwarmMetrics:
    runs_total: Counter
    active_runs: UpDownCounter
    run_duration: Histogram
    task_duration: Histogram
    activity_retries: Counter
    queue_schedule_latency: Histogram
    model_requests: Counter
    model_tokens: Counter
    model_cost: Counter
    tool_calls: Counter
    policy_denied: Counter
    approval_wait: Histogram
    sse_connections: UpDownCounter
    projection_lag: Histogram
    outbox_pending: UpDownCounter
    webhook_deliveries: Counter

    @classmethod
    def create(cls, component: str) -> SwarmMetrics:
        meter = get_meter(component)
        return cls(
            runs_total=meter.create_counter("swarm_runs_total"),
            active_runs=meter.create_up_down_counter("swarm_active_runs"),
            run_duration=meter.create_histogram("swarm_run_duration_seconds"),
            task_duration=meter.create_histogram("swarm_task_duration_seconds"),
            activity_retries=meter.create_counter("swarm_activity_retries_total"),
            queue_schedule_latency=meter.create_histogram(
                "swarm_queue_schedule_latency_seconds"
            ),
            model_requests=meter.create_counter("swarm_model_requests_total"),
            model_tokens=meter.create_counter("swarm_model_tokens_total"),
            model_cost=meter.create_counter("swarm_model_cost_usd_total"),
            tool_calls=meter.create_counter("swarm_tool_calls_total"),
            policy_denied=meter.create_counter("swarm_policy_denied_total"),
            approval_wait=meter.create_histogram("swarm_approval_wait_seconds"),
            sse_connections=meter.create_up_down_counter("swarm_sse_connections"),
            projection_lag=meter.create_histogram("swarm_event_projection_lag_seconds"),
            outbox_pending=meter.create_up_down_counter("swarm_outbox_pending"),
            webhook_deliveries=meter.create_counter("swarm_webhook_delivery_total"),
        )


class JsonRedactingFormatter(logging.Formatter):
    _SENSITIVE = frozenset(
        {"authorization", "password", "secret", "token", "api_key", "private_key"}
    )
    _MESSAGE_SECRET = re.compile(
        r"(?i)(authorization|password|secret|token|api[_-]?key|private[_-]?key)"
        r"(\s*[:=]\s*|\s+)(bearer\s+)?[^\s,;]+"
    )

    def format(self, record: logging.LogRecord) -> str:
        document: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", record.name),
            "trace_id": getattr(record, "trace_id", None),
            "run_id": getattr(record, "run_id", None),
            "task_id": getattr(record, "task_id", None),
            "event": getattr(record, "event", record.name),
            "message": self._redact_message(record.getMessage()),
        }
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            document["fields"] = self._redact(fields)
        if record.exc_info and record.exc_info[0] is not None:
            document["exception"] = record.exc_info[0].__name__
        return json.dumps(document, ensure_ascii=False, separators=(",", ":"))

    def _redact(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: "[REDACTED]" if key.lower() in self._SENSITIVE else self._redact(item)
                for key, item in value.items()
            }
        if isinstance(value, list | tuple):
            return [self._redact(item) for item in value]
        return value

    def _redact_message(self, value: str) -> str:
        return self._MESSAGE_SECRET.sub(lambda match: f"{match.group(1)}=[REDACTED]", value)


def configure_json_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonRedactingFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
