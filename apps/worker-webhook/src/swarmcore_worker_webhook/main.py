from __future__ import annotations

import asyncio
import socket

from pydantic_settings import BaseSettings, SettingsConfigDict
from swarmcore_governance import OpaPolicyEngine, RolePolicyEngine, VaultSecretProvider
from swarmcore_observability import SwarmMetrics, configure_json_logging, configure_telemetry
from swarmcore_persistence import Database

from .worker import WebhookWorker


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://swarmcore:swarmcore@localhost:5433/swarmcore"
    webhook_poll_seconds: float = 0.5
    webhook_allowed_hosts: frozenset[str] = frozenset()
    vault_address: str = "http://localhost:8200"
    vault_token: str = ""
    vault_kubernetes_role: str = ""
    vault_kubernetes_jwt_path: str = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    vault_kubernetes_auth_mount: str = "kubernetes"
    policy_mode: str = "local"
    opa_decision_url: str = "http://localhost:8181/v1/data/swarmcore/decision"
    otlp_endpoint: str = "http://localhost:4317"
    telemetry_enabled: bool = True


async def serve() -> None:
    settings = Settings()
    if not settings.vault_token and not settings.vault_kubernetes_role:
        raise RuntimeError("Webhook Worker requires Vault authentication")
    telemetry = configure_telemetry(
        "worker-webhook", endpoint=settings.otlp_endpoint, enabled=settings.telemetry_enabled
    )
    database = Database(settings.database_url)
    worker = WebhookWorker(
        database.sessions,
        OpaPolicyEngine(settings.opa_decision_url)
        if settings.policy_mode == "opa"
        else RolePolicyEngine(),
        VaultSecretProvider(
            settings.vault_address,
            settings.vault_token,
            kubernetes_role=settings.vault_kubernetes_role,
            kubernetes_jwt_path=settings.vault_kubernetes_jwt_path,
            kubernetes_auth_mount=settings.vault_kubernetes_auth_mount,
        ),
        worker_id=socket.gethostname(),
        allowed_hosts=settings.webhook_allowed_hosts,
        metrics=SwarmMetrics.create("worker-webhook"),
    )
    try:
        while True:
            count = await worker.run_once()
            if count == 0:
                await asyncio.sleep(settings.webhook_poll_seconds)
    finally:
        await database.dispose()
        telemetry.shutdown()


def run() -> None:
    configure_json_logging()
    asyncio.run(serve())
