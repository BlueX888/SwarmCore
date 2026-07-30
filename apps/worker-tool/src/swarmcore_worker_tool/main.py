from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from swarmcore_application import capability_executors
from swarmcore_governance import OpaPolicyEngine, RolePolicyEngine, VaultSecretProvider
from swarmcore_observability import configure_json_logging, configure_telemetry
from swarmcore_persistence import Database, PostgresEffectJournal
from swarmcore_registry import builtin_registry
from swarmcore_tool_gateway import (
    CapabilityTokenIssuer,
    FilesystemExecutorMode,
    FilesystemToolConfig,
    ToolGateway,
    assemble_tool_executors,
)
from swarmcore_tool_gateway.filesystem import DEFAULT_DENY_NAMES
from temporalio.client import Client
from temporalio.contrib.opentelemetry import TracingInterceptor
from temporalio.worker import Worker

from .activities import ToolActivities


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://swarmcore:swarmcore@localhost:5433/swarmcore"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    tool_task_queue: str = "tool-trusted"
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
    deployment_mode: Literal["local", "production"] = "local"
    filesystem_tools_enabled: bool = False
    filesystem_root: str = ".tmp/filesystem"
    filesystem_allowed_mounts: list[str] = Field(default_factory=lambda: ["workspace"])
    filesystem_max_read_bytes: int = 1_048_576
    filesystem_max_write_bytes: int = 1_048_576
    filesystem_max_list_entries: int = 1_000
    filesystem_deny_names: list[str] = Field(
        default_factory=lambda: sorted(DEFAULT_DENY_NAMES)
    )
    filesystem_executor_mode: Literal["disabled", "local", "sandbox"] = "disabled"
    filesystem_sandbox_url: str = "http://localhost:8092"
    filesystem_sandbox_image: str = ""
    filesystem_sandbox_capability_secret: str = ""
    filesystem_sandbox_timeout_seconds: int = 60
    github_token: str = ""
    github_api_url: str = ""
    calibration_sandbox_enabled: bool = False
    calibration_sandbox_image: str = ""
    calibration_sandbox_docker_binary: str = "docker"
    calibration_sandbox_timeout_seconds: int = 600
    supplier_risk_allowed_hosts: list[str] = Field(
        default_factory=lambda: [
            "www.ccgp.gov.cn",
            "api.qichacha.com",
            "open.api.tianyancha.com",
        ]
    )
    supplier_risk_timeout_seconds: int = 30
    worker_max_concurrent_activities: int = Field(default=32, ge=1)
    worker_max_activity_polls: int = Field(default=5, ge=1)

    def filesystem_config(self) -> FilesystemToolConfig:
        return FilesystemToolConfig(
            enabled=self.filesystem_tools_enabled,
            root=Path(self.filesystem_root),
            allowed_mounts=frozenset(self.filesystem_allowed_mounts),
            max_read_bytes=self.filesystem_max_read_bytes,
            max_write_bytes=self.filesystem_max_write_bytes,
            max_list_entries=self.filesystem_max_list_entries,
            deny_names=frozenset(self.filesystem_deny_names),
            mode=FilesystemExecutorMode(self.filesystem_executor_mode),
            deployment_mode=self.deployment_mode,
            sandbox_base_url=self.filesystem_sandbox_url,
            sandbox_image=self.filesystem_sandbox_image,
            sandbox_capability_secret=self.filesystem_sandbox_capability_secret
            or self.tool_capability_secret,
            sandbox_timeout_seconds=self.filesystem_sandbox_timeout_seconds,
        )

    @field_validator(
        "filesystem_allowed_mounts",
        "filesystem_deny_names",
        "supplier_risk_allowed_hosts",
        mode="before",
    )
    @classmethod
    def _split_csv(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_filesystem_boundary(self) -> Settings:
        if self.deployment_mode == "production" and self.filesystem_executor_mode == "local":
            raise ValueError("production worker-tool forbids local filesystem executor mode")
        self.filesystem_config().validate()
        return self


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
        assemble_tool_executors(
            filesystem=settings.filesystem_config(),
            extra=capability_executors(
                database.sessions,
                github_token=settings.github_token,
                github_api_url=settings.github_api_url,
                calibration_sandbox_enabled=settings.calibration_sandbox_enabled,
                calibration_sandbox_image=settings.calibration_sandbox_image,
                calibration_sandbox_docker_binary=settings.calibration_sandbox_docker_binary,
                calibration_sandbox_timeout_seconds=(
                    settings.calibration_sandbox_timeout_seconds
                ),
                supplier_risk_allowed_hosts=tuple(settings.supplier_risk_allowed_hosts),
                supplier_risk_timeout_seconds=settings.supplier_risk_timeout_seconds,
            ),
        ),
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
        task_queue=settings.tool_task_queue,
        activities=[activities.execute_tool, activities.compensate_tool],
        max_concurrent_activities=settings.worker_max_concurrent_activities,
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
