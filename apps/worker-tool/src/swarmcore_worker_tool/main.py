from __future__ import annotations

import asyncio

from pydantic_settings import BaseSettings, SettingsConfigDict
from swarmcore_application import capability_executors
from swarmcore_governance import OpaPolicyEngine, RolePolicyEngine, VaultSecretProvider
from swarmcore_observability import configure_json_logging, configure_telemetry
from swarmcore_persistence import Database, PostgresEffectJournal
from swarmcore_registry import builtin_registry
from swarmcore_tool_gateway import CapabilityTokenIssuer, ToolGateway, builtin_executors
from temporalio.client import Client
from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.worker import Worker

from .activities import ToolActivities


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://swarmcore:swarmcore@localhost:5433/swarmcore"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    tool_capability_secret: str = "development-only-capability-secret-32-bytes"
    otlp_endpoint: str = "http://localhost:4317"
    telemetry_enabled: bool = True
    vault_address: str = "http://localhost:8200"
    vault_token: str = ""
    vault_kubernetes_role: str = ""
    vault_kubernetes_jwt_path: str = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    vault_kubernetes_auth_mount: str = "kubernetes"
    policy_mode: str = "local"
    opa_decision_url: str = "http://localhost:8181/v1/data/swarmcore/decision"


async def serve() -> None:
    settings = Settings()
    telemetry = configure_telemetry(
        "worker-tool", endpoint=settings.otlp_endpoint, enabled=settings.telemetry_enabled
    )
    database = Database(settings.database_url)
    temporal = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
        interceptors=[TracingInterceptor()],
    )
    gateway = ToolGateway(
        builtin_registry(),
        CapabilityTokenIssuer(settings.tool_capability_secret),
        PostgresEffectJournal(database.sessions),
        {**builtin_executors(), **capability_executors(database.sessions)},
        secrets=(
            VaultSecretProvider(
                settings.vault_address,
                settings.vault_token,
                kubernetes_role=settings.vault_kubernetes_role,
                kubernetes_jwt_path=settings.vault_kubernetes_jwt_path,
                kubernetes_auth_mount=settings.vault_kubernetes_auth_mount,
            )
            if settings.vault_token or settings.vault_kubernetes_role
            else None
        ),
        policy=(
            OpaPolicyEngine(settings.opa_decision_url)
            if settings.policy_mode == "opa"
            else RolePolicyEngine()
        ),
    )
    activities = ToolActivities(gateway)
    worker = Worker(
        temporal,
        task_queue="tool-trusted",
        activities=[activities.execute_tool, activities.compensate_tool],
    )
    try:
        await worker.run()
    finally:
        await database.dispose()
        telemetry.shutdown()


def run() -> None:
    configure_json_logging()
    asyncio.run(serve())
