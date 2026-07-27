from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from swarmcore_application import capability_executors
from swarmcore_domain import uuid7
from swarmcore_governance import (
    OpaPolicyEngine,
    RolePolicyEngine,
    VaultSecretProvider,
    WorkloadTls,
)
from swarmcore_observability import (
    SwarmMetrics,
    configure_json_logging,
    configure_telemetry,
    get_tracer,
)
from swarmcore_persistence import (
    Database,
    EventRepository,
    PostgresEffectJournal,
    tenant_transaction,
)
from swarmcore_registry import builtin_registry
from swarmcore_tool_gateway import (
    AuditEvent,
    CapabilityTokenIssuer,
    EffectConflict,
    EffectInProgress,
    FilesystemExecutorMode,
    FilesystemToolConfig,
    GatewayError,
    TokenError,
    ToolGateway,
    ToolInvocation,
    assemble_tool_executors,
)
from swarmcore_tool_gateway.filesystem import DEFAULT_DENY_NAMES


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://swarmcore:swarmcore@localhost:5433/swarmcore"
    tool_capability_secret: str = "development-only-capability-secret-32-bytes"
    tool_gateway_host: str = "127.0.0.1"
    tool_gateway_port: int = 8090
    vault_address: str = "http://localhost:8200"
    vault_token: str = ""
    vault_kubernetes_role: str = ""
    vault_kubernetes_jwt_path: str = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    vault_kubernetes_auth_mount: str = "kubernetes"
    policy_mode: str = "local"
    opa_decision_url: str = "http://localhost:8181/v1/data/swarmcore/decision"
    otlp_endpoint: str = "http://localhost:4317"
    telemetry_enabled: bool = True
    deployment_mode: Literal["local", "production"] = "local"
    workload_tls_ca_file: str = ""
    workload_tls_cert_file: str = ""
    workload_tls_key_file: str = ""
    filesystem_tools_enabled: bool = False
    filesystem_root: str = ".tmp/filesystem"
    filesystem_allowed_mounts: list[str] = Field(default_factory=lambda: ["workspace"])
    filesystem_max_read_bytes: int = 1_048_576
    filesystem_max_write_bytes: int = 1_048_576
    filesystem_max_list_entries: int = 1_000
    filesystem_deny_names: list[str] = Field(default_factory=lambda: sorted(DEFAULT_DENY_NAMES))
    filesystem_executor_mode: Literal["disabled", "local", "sandbox"] = "disabled"
    filesystem_sandbox_url: str = "http://localhost:8092"
    filesystem_sandbox_image: str = ""
    filesystem_sandbox_capability_secret: str = ""
    filesystem_sandbox_timeout_seconds: int = 60

    def workload_tls(self) -> WorkloadTls:
        return WorkloadTls(
            self.workload_tls_ca_file,
            self.workload_tls_cert_file,
            self.workload_tls_key_file,
        )

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

    @field_validator("filesystem_allowed_mounts", "filesystem_deny_names", mode="before")
    @classmethod
    def _split_csv(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_production_boundary(self) -> Settings:
        self.workload_tls().validate(required=self.deployment_mode == "production")
        if self.deployment_mode == "production":
            if self.tool_capability_secret.startswith("development-"):
                raise ValueError("production Tool Gateway requires a managed capability secret")
            if self.policy_mode != "opa":
                raise ValueError("production Tool Gateway requires OPA")
            if not self.vault_kubernetes_role:
                raise ValueError("production Tool Gateway requires Vault Kubernetes auth")
            if self.filesystem_executor_mode == "local":
                raise ValueError("production Tool Gateway forbids local filesystem executor mode")
        self.filesystem_config().validate()
        return self


class PostgresToolAuditSink:
    def __init__(self, database: Database) -> None:
        self._database = database
        self._events = EventRepository()

    async def record(self, event: AuditEvent) -> None:
        tenant_id = UUID(event.tenant_id)
        project_id = UUID(event.project_id)
        async with tenant_transaction(
            self._database.sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            await self._events.append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=UUID(event.run_id),
                transition_id=uuid7(),
                event_type=event.type,
                payload={
                    "nodeKey": event.node_key,
                    "toolRef": event.tool_ref,
                    "effectId": event.effect_id,
                    **event.data,
                },
                occurred_at=datetime.now(UTC),
            )


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or Settings()
    metrics = SwarmMetrics.create("tool-gateway")
    token_issuer = CapabilityTokenIssuer(configured.tool_capability_secret)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database = Database(configured.database_url)
        app.state.database = database
        app.state.gateway = ToolGateway(
            builtin_registry(),
            token_issuer,
            PostgresEffectJournal(database.sessions),
            assemble_tool_executors(
                filesystem=configured.filesystem_config(),
                extra=capability_executors(database.sessions),
            ),
            PostgresToolAuditSink(database),
            secrets=(
                VaultSecretProvider(
                    configured.vault_address,
                    configured.vault_token,
                    kubernetes_role=configured.vault_kubernetes_role,
                    kubernetes_jwt_path=configured.vault_kubernetes_jwt_path,
                    kubernetes_auth_mount=configured.vault_kubernetes_auth_mount,
                )
                if configured.vault_token or configured.vault_kubernetes_role
                else None
            ),
            policy=(
                OpaPolicyEngine(configured.opa_decision_url)
                if configured.policy_mode == "opa"
                else RolePolicyEngine()
            ),
        )
        try:
            yield
        finally:
            await database.dispose()

    app = FastAPI(title="SwarmCore Tool Gateway", lifespan=lifespan)

    @app.post("/internal/v1/tools/invoke")
    async def invoke(body: ToolInvocation, request: Request) -> dict[str, Any]:
        gateway: ToolGateway = request.app.state.gateway
        try:
            capability = token_issuer.verify(body.token)
        except TokenError as exc:
            metrics.tool_calls.add(1, {"tool": "invalid", "status": "denied"})
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        labels = {"tool": capability.tool_ref}
        span = get_tracer("tool-gateway").start_span(
            "tool.call",
            attributes={
                "tenant.id": capability.tenant_id,
                "project.id": capability.project_id,
                "swarm.run.id": capability.run_id,
                "swarm.task.id": capability.execution_id,
                "tool.name": capability.tool_ref,
            },
        )
        try:
            result = await gateway.invoke(body)
            metrics.tool_calls.add(1, {**labels, "status": "succeeded"})
            span.end()
            return result
        except EffectInProgress as exc:
            metrics.tool_calls.add(1, {**labels, "status": "in_progress"})
            span.set_attribute("error.type", type(exc).__name__)
            span.end()
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except EffectConflict as exc:
            metrics.tool_calls.add(1, {**labels, "status": "conflict"})
            span.set_attribute("error.type", type(exc).__name__)
            span.end()
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except GatewayError as exc:
            metrics.tool_calls.add(1, {**labels, "status": "denied"})
            span.set_attribute("error.type", type(exc).__name__)
            span.end()
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.get("/healthz")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/internal/v1/readiness")
    async def readiness(request: Request) -> dict[str, Any]:
        gateway: ToolGateway = request.app.state.gateway
        return {"tools": await gateway.readiness()}

    return app


def run() -> None:
    configure_json_logging()
    settings = Settings()
    telemetry = configure_telemetry(
        "tool-gateway", endpoint=settings.otlp_endpoint, enabled=settings.telemetry_enabled
    )
    try:
        uvicorn.run(
            create_app(settings),
            host=settings.tool_gateway_host,
            port=settings.tool_gateway_port,
            **settings.workload_tls().uvicorn_options(),
        )
    finally:
        telemetry.shutdown()
