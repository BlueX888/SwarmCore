from __future__ import annotations

import asyncio
import socket

from pydantic_settings import BaseSettings, SettingsConfigDict
from swarmcore_observability import SwarmMetrics, configure_json_logging, configure_telemetry
from swarmcore_persistence import Database
from temporalio.client import Client
from temporalio.contrib.opentelemetry import TracingInterceptor

from .dispatcher import CommandDispatcher


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://swarmcore:swarmcore@localhost:5433/swarmcore"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "swarm-control"
    agent_task_queue: str = "agent-general"
    tool_task_queue: str = "tool-trusted"
    dispatcher_poll_seconds: float = 0.5
    otlp_endpoint: str = "http://localhost:4317"
    telemetry_enabled: bool = True


async def serve() -> None:
    settings = Settings()
    telemetry = configure_telemetry(
        "command-dispatcher", endpoint=settings.otlp_endpoint, enabled=settings.telemetry_enabled
    )
    database = Database(settings.database_url)
    temporal = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
        interceptors=[TracingInterceptor()],
    )
    dispatcher = CommandDispatcher(
        database.sessions,
        temporal,
        worker_id=socket.gethostname(),
        task_queue=settings.temporal_task_queue,
        agent_task_queue=settings.agent_task_queue,
        tool_task_queue=settings.tool_task_queue,
        metrics=SwarmMetrics.create("command-dispatcher"),
    )
    try:
        while True:
            count = await dispatcher.run_once()
            if count == 0:
                await asyncio.sleep(settings.dispatcher_poll_seconds)
    finally:
        await database.dispose()
        telemetry.shutdown()


def run() -> None:
    configure_json_logging()
    asyncio.run(serve())
