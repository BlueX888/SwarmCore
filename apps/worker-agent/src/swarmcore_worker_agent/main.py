from __future__ import annotations

import asyncio
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from swarmcore_adapter_agno import AgnoAdapter
from swarmcore_governance import ModelCapabilityIssuer, WorkloadTls
from swarmcore_observability import SwarmMetrics, configure_json_logging, configure_telemetry
from swarmcore_registry import builtin_registry
from temporalio.client import Client
from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.worker import Worker

from .activities import AgentActivities
from .fake import DeterministicFakeAgentAdapter
from .gateway_proxy import HttpGatewayProxyFactory
from .model_gateway import GatewayModelResolver


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    models: dict[str, str] = Field(
        default_factory=lambda: {"model://general": "openai:gpt-4o-mini"}
    )
    otlp_endpoint: str = "http://localhost:4317"
    telemetry_enabled: bool = True
    use_fake_agent: bool = False
    tool_gateway_url: str = "http://localhost:8090"
    model_gateway_url: str = "http://localhost:8093"
    model_capability_secret: str = "development-model-capability-secret-32-bytes"
    deployment_mode: Literal["local", "production"] = "local"
    workload_tls_ca_file: str = ""
    workload_tls_cert_file: str = ""
    workload_tls_key_file: str = ""

    def workload_tls(self) -> WorkloadTls:
        return WorkloadTls(
            self.workload_tls_ca_file,
            self.workload_tls_cert_file,
            self.workload_tls_key_file,
        )

    @model_validator(mode="after")
    def validate_production_boundary(self) -> Settings:
        self.workload_tls().validate(required=self.deployment_mode == "production")
        if self.deployment_mode == "production":
            if self.model_capability_secret.startswith("development-"):
                raise ValueError("production Agent Worker requires a managed capability secret")
            if not self.tool_gateway_url.startswith("https://"):
                raise ValueError("production Agent Worker requires HTTPS Tool Gateway")
            if not self.model_gateway_url.startswith("https://"):
                raise ValueError("production Agent Worker requires HTTPS Model Gateway")
        return self


async def serve() -> None:
    settings = Settings()
    workload_tls = settings.workload_tls()
    telemetry = configure_telemetry(
        "worker-agent", endpoint=settings.otlp_endpoint, enabled=settings.telemetry_enabled
    )
    temporal = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
        interceptors=[TracingInterceptor()],
    )
    adapter = (
        DeterministicFakeAgentAdapter()
        if settings.use_fake_agent
        else AgnoAdapter(
            GatewayModelResolver(
                settings.model_gateway_url,
                ModelCapabilityIssuer(settings.model_capability_secret.encode()),
                frozenset(settings.models),
                workload_tls,
            ),
            HttpGatewayProxyFactory(
                settings.tool_gateway_url,
                builtin_registry(),
                workload_tls=workload_tls,
            ),
        )
    )
    activities = AgentActivities(adapter, SwarmMetrics.create("worker-agent"))
    worker = Worker(
        temporal,
        task_queue="agent-general",
        activities=[activities.execute_agent, activities.execute_team],
    )
    try:
        await worker.run()
    finally:
        telemetry.shutdown()


def run() -> None:
    configure_json_logging()
    asyncio.run(serve())
