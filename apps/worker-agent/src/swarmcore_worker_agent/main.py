from __future__ import annotations

import asyncio
from typing import Any, Literal

import uvicorn
from fastapi import FastAPI
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
    agent_task_queue: str = "agent-general"
    models: dict[str, str] = Field(
        default_factory=lambda: {
            "model://general": "openai:gpt-4o-mini",
            "model://contract-performance-reasoning": "openai:gpt-4o-mini",
            "model://document-nlp": "openai:gpt-4o",
            "model://deepseek-v4-flash": "DeepSeek-V4-Flash",
            "model://deepseek-v4-pro": "DeepSeek-V4-Pro",
            "model://kimi-k2.5": "kimi-k2.5",
            "model://kimi-k2.7-code": "kimi-k2.7-code",
        }
    )
    otlp_endpoint: str = "http://localhost:4317"
    telemetry_enabled: bool = True
    use_fake_agent: bool = False
    tool_gateway_url: str = "http://localhost:8090"
    model_gateway_url: str = "http://localhost:8093"
    model_gateway_timeout_seconds: float = 300
    agent_model_max_output_tokens: int = Field(default=16384, ge=1024, le=65536)
    worker_max_concurrent_activities: int = Field(default=32, ge=1)
    worker_max_activity_polls: int = Field(default=5, ge=1)
    model_capability_secret: str = "development-model-capability-secret-32-bytes"
    agent_readiness_host: str = "127.0.0.1"
    agent_readiness_port: int = 8094
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
            if self.use_fake_agent:
                raise ValueError("production Agent Worker cannot use the fake agent")
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
                settings.model_gateway_timeout_seconds,
                settings.agent_model_max_output_tokens,
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
        task_queue=settings.agent_task_queue,
        activities=[activities.execute_agent, activities.execute_team],
        max_concurrent_activities=settings.worker_max_concurrent_activities,
        max_concurrent_activity_task_polls=settings.worker_max_activity_polls,
    )
    readiness_server = uvicorn.Server(
        uvicorn.Config(
            create_readiness_app(adapter, model_refs=tuple(sorted(settings.models))),
            host=settings.agent_readiness_host,
            port=settings.agent_readiness_port,
            log_level="warning",
        )
    )
    readiness_task = asyncio.create_task(readiness_server.serve())
    try:
        await worker.run()
    finally:
        readiness_server.should_exit = True
        await readiness_task
        telemetry.shutdown()


def create_readiness_app(
    adapter: Any, *, model_refs: tuple[str, ...] = ()
) -> FastAPI:
    app = FastAPI(title="SwarmCore Agent Adapter Readiness")

    @app.get("/internal/v1/readiness")
    async def readiness() -> dict[str, Any]:
        return {
            "adapters": [
                {
                    "runtime": "fake-deterministic"
                    if isinstance(adapter, DeterministicFakeAgentAdapter)
                    else "agno",
                    "healthy": True,
                }
            ],
            "modelRefs": list(model_refs),
        }

    return app


def run() -> None:
    configure_json_logging()
    asyncio.run(serve())
