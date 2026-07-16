from __future__ import annotations

import asyncio
import logging

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from swarmcore_adapter_agno import AgnoAdapter
from swarmcore_observability import configure_telemetry
from temporalio.client import Client
from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.worker import Worker

from .activities import AgentActivities, StaticModelResolver
from .fake import DeterministicFakeAgentAdapter


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


async def serve() -> None:
    settings = Settings()
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
        else AgnoAdapter(StaticModelResolver(settings.models))
    )
    activities = AgentActivities(adapter)
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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(serve())
