from __future__ import annotations

from dataclasses import dataclass

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
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
