from __future__ import annotations

import asyncio
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from swarmcore_observability import SwarmMetrics, configure_json_logging, configure_telemetry
from swarmcore_persistence import Database
from swarmcore_runtime_temporal import (
    ControlActivities,
    DocumentProcessingWorkflow,
    SwarmRunWorkflow,
)
from swarmcore_tool_gateway import CapabilityTokenIssuer
from temporalio.client import Client
from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.worker import Worker

from .adapters import GatewayCapabilityIssuer, PostgresPlanStore, PostgresTransitionProjector
from .document_processing import DocumentProcessingActivities


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://swarmcore:swarmcore@localhost:5433/swarmcore"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "swarm-control"
    otlp_endpoint: str = "http://localhost:4317"
    telemetry_enabled: bool = True
    tool_capability_secret: str = "development-only-capability-secret-32-bytes"
    artifact_root: str = ".tmp/artifacts"


async def serve() -> None:
    settings = Settings()
    telemetry = configure_telemetry(
        "worker-control", endpoint=settings.otlp_endpoint, enabled=settings.telemetry_enabled
    )
    database = Database(settings.database_url)
    temporal = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
        interceptors=[TracingInterceptor()],
    )
    activities = ControlActivities(
        PostgresPlanStore(database.sessions),
        PostgresTransitionProjector(
            database.sessions, SwarmMetrics.create("worker-control")
        ),
        GatewayCapabilityIssuer(CapabilityTokenIssuer(settings.tool_capability_secret)),
    )
    document_activities = DocumentProcessingActivities(
        database.sessions,
        artifact_root=Path(settings.artifact_root),
    )
    worker = Worker(
        temporal,
        task_queue=settings.temporal_task_queue,
        workflows=[SwarmRunWorkflow, DocumentProcessingWorkflow],
        activities=[
            activities.load_execution_plan,
            activities.project_transition,
            activities.issue_tool_capability,
            activities.execute_control_node,
            document_activities.plan,
            document_activities.process_group,
            document_activities.finalize,
        ],
    )
    try:
        await worker.run()
    finally:
        await database.dispose()
        telemetry.shutdown()


def run() -> None:
    configure_json_logging()
    asyncio.run(serve())
