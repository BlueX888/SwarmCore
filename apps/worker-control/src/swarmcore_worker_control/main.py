from __future__ import annotations

import asyncio
import importlib
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from swarmcore_governance import LocalArtifactStore, S3ArtifactStore
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
    artifact_store: Literal["local", "s3"] = "local"
    artifact_s3_bucket: str = ""
    artifact_s3_endpoint: str = ""
    artifact_s3_region: str = ""
    artifact_s3_kms_key_id: str = ""
    deployment_mode: Literal["local", "production"] = "local"
    worker_max_concurrent_workflows: int = Field(default=100, ge=1)
    worker_max_concurrent_activities: int = Field(default=16, ge=1)
    worker_max_workflow_polls: int = Field(default=5, ge=1)
    worker_max_activity_polls: int = Field(default=5, ge=1)

    @model_validator(mode="after")
    def validate_artifact_store(self) -> Settings:
        if self.artifact_store == "s3" and not self.artifact_s3_bucket:
            raise ValueError("S3 artifact store requires a bucket")
        if self.deployment_mode == "production" and self.artifact_store != "s3":
            raise ValueError("production Control Worker requires shared S3 artifact storage")
        return self


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
        artifact_store=_artifact_store(settings),
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
        max_concurrent_workflow_tasks=settings.worker_max_concurrent_workflows,
        max_concurrent_activities=settings.worker_max_concurrent_activities,
        max_concurrent_workflow_task_polls=settings.worker_max_workflow_polls,
        max_concurrent_activity_task_polls=settings.worker_max_activity_polls,
    )
    try:
        await worker.run()
    finally:
        await database.dispose()
        telemetry.shutdown()


def run() -> None:
    configure_json_logging()
    asyncio.run(serve())


def _artifact_store(settings: Settings) -> Any:
    if settings.artifact_store == "local":
        return LocalArtifactStore(Path(settings.artifact_root))
    boto3 = importlib.import_module("boto3")
    client = boto3.client(
        "s3",
        endpoint_url=settings.artifact_s3_endpoint or None,
        region_name=settings.artifact_s3_region or None,
    )
    return S3ArtifactStore(
        client,
        settings.artifact_s3_bucket,
        kms_key_id=settings.artifact_s3_kms_key_id,
    )
