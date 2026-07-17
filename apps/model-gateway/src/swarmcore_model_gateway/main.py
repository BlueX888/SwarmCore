from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, Literal, cast
from urllib.request import Request, urlopen
from uuid import UUID

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi import Request as HttpRequest
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from swarmcore_domain import uuid7
from swarmcore_governance import (
    ModelCapabilityIssuer,
    OpaPolicyEngine,
    PolicyRequest,
    PolicySubject,
    RolePolicyEngine,
    SecretScanner,
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
    AuditRepository,
    Database,
    EventRepository,
    tenant_transaction,
)
from swarmcore_persistence.models import ModelUsageRecord, Run


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://swarmcore:swarmcore@localhost:5433/swarmcore"
    model_capability_secret: str = "development-model-capability-secret-32-bytes"
    model_routes: dict[str, str] = {"model://general": "openai/gpt-4o-mini"}
    model_price_version: str = "local-price:v1"
    litellm_url: str = "http://localhost:4000"
    litellm_timeout_seconds: float = 120
    litellm_secret_ref: str = "secret://platform/litellm"
    vault_address: str = "http://localhost:8200"
    vault_token: str = ""
    vault_kubernetes_role: str = ""
    vault_kubernetes_jwt_path: str = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    vault_kubernetes_auth_mount: str = "kubernetes"
    policy_mode: str = "local"
    opa_decision_url: str = "http://localhost:8181/v1/data/swarmcore/decision"
    model_gateway_host: str = "127.0.0.1"
    model_gateway_port: int = 8093
    otlp_endpoint: str = "http://localhost:4317"
    telemetry_enabled: bool = True
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
                raise ValueError("production Model Gateway requires a managed capability secret")
            if self.policy_mode != "opa":
                raise ValueError("production Model Gateway requires OPA")
            if not self.vault_kubernetes_role:
                raise ValueError("production Model Gateway requires Vault Kubernetes auth")
        return self


class InvokeBody(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    capability_token: str = Field(alias="capabilityToken")
    messages: list[dict[str, Any]]
    max_tokens: int = Field(alias="maxTokens", ge=1, le=1_000_000)
    parameters: dict[str, Any] = Field(default_factory=dict)


class OpenAiInvokeBody(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str
    messages: list[dict[str, Any]]
    max_tokens: int | None = Field(default=None, ge=1, le=1_000_000)
    stream: bool = False


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or Settings()
    tokens = ModelCapabilityIssuer(configured.model_capability_secret.encode())
    policy = (
        OpaPolicyEngine(configured.opa_decision_url)
        if configured.policy_mode == "opa"
        else RolePolicyEngine()
    )
    secrets = (
        VaultSecretProvider(
            configured.vault_address,
            configured.vault_token,
            kubernetes_role=configured.vault_kubernetes_role,
            kubernetes_jwt_path=configured.vault_kubernetes_jwt_path,
            kubernetes_auth_mount=configured.vault_kubernetes_auth_mount,
        )
        if configured.vault_token or configured.vault_kubernetes_role
        else None
    )
    metrics = SwarmMetrics.create("model-gateway")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.database = Database(configured.database_url)
        try:
            yield
        finally:
            await app.state.database.dispose()

    app = FastAPI(title="SwarmCore Model Gateway", lifespan=lifespan)

    async def execute(body: InvokeBody, request: HttpRequest) -> dict[str, Any]:
        try:
            capability = tokens.verify(body.capability_token)
            provider_model = configured.model_routes[capability.logical_model]
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        decision = (
            await policy.evaluate(
                PolicyRequest(
                    subject=PolicySubject(
                        id=capability.subject_id,
                        tenantId=capability.tenant_id,
                        roles=("workload",),
                    ),
                    action="model.invoke",
                    resource={
                        "projectId": capability.project_id,
                        "logicalModel": capability.logical_model,
                        "providerModel": provider_model,
                    },
                    context={"runId": capability.run_id},
                )
            )
        ).enforce()
        tenant_id = UUID(capability.tenant_id)
        project_id = UUID(capability.project_id)
        run_id = UUID(capability.run_id)
        request_id = _model_request_id(capability.jti, body)
        database: Database = request.app.state.database
        await _reserve(
            database,
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            max_tokens=body.max_tokens,
            request_id=request_id,
        )
        provider = provider_model.partition("/")[0]
        span = get_tracer("model-gateway").start_span(
            "llm.request",
            attributes={
                "tenant.id": capability.tenant_id,
                "project.id": capability.project_id,
                "swarm.run.id": capability.run_id,
                "swarm.task.id": capability.task_execution_id,
                "model.logical_name": capability.logical_model,
                "model.provider": provider,
            },
        )
        try:
            if secrets is None:
                result = await asyncio.to_thread(
                    _litellm,
                    configured.litellm_url,
                    "",
                    provider_model,
                    body,
                    configured.litellm_timeout_seconds,
                )
            else:
                async with secrets.lease(configured.litellm_secret_ref) as lease:
                    key = lease.values.get("apiKey")
                    if key is None:
                        raise RuntimeError("LiteLLM Secret must contain apiKey")
                    result = await asyncio.to_thread(
                        _litellm,
                        configured.litellm_url,
                        key,
                        provider_model,
                        body,
                        configured.litellm_timeout_seconds,
                    )
                    SecretScanner(lease.values).assert_clean(
                        json.dumps(result, ensure_ascii=False).encode()
                    )
        except Exception:
            metrics.model_requests.add(
                1,
                {"provider": provider, "model": capability.logical_model, "status": "failed"},
            )
            span.set_attribute("error.type", "provider_error")
            span.end()
            await _release(
                database,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
                reserved=body.max_tokens,
                request_id=request_id,
            )
            raise
        usage = cast(dict[str, Any], result.get("usage", {}))
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
        cost = float(result.get("response_cost", 0))
        try:
            await _commit(
                database,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
                capability_jti=request_id,
                actor_id=capability.subject_id,
                logical_model=capability.logical_model,
                provider_model=provider_model,
                price_version=configured.model_price_version,
                reserved=body.max_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                policy_revision=decision.policy_revision,
            )
        except Exception:
            span.set_attribute("error.type", "usage_commit_error")
            span.end()
            await _release(
                database,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
                reserved=body.max_tokens,
                request_id=request_id,
            )
            raise
        labels = {"provider": provider, "model": capability.logical_model}
        metrics.model_requests.add(1, {**labels, "status": "succeeded"})
        metrics.model_tokens.add(input_tokens, {**labels, "direction": "input"})
        metrics.model_tokens.add(output_tokens, {**labels, "direction": "output"})
        metrics.model_cost.add(cost, labels)
        span.set_attribute("token.input", input_tokens)
        span.set_attribute("token.output", output_tokens)
        span.set_attribute("budget.cost_usd", cost)
        span.end()
        return result

    @app.post("/internal/v1/models:invoke")
    async def invoke(body: InvokeBody, request: HttpRequest) -> dict[str, Any]:
        result = await execute(body, request)
        usage = cast(dict[str, Any], result.get("usage", {}))
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
        cost = float(result.get("response_cost", 0))
        return {
            "id": result.get("id"),
            "model": result.get("model"),
            "choices": result.get("choices", []),
            "usage": {
                "inputTokens": input_tokens,
                "outputTokens": output_tokens,
                "costUsd": cost,
                "priceVersion": configured.model_price_version,
            },
        }

    @app.post("/v1/chat/completions")
    async def openai_invoke(
        body: OpenAiInvokeBody,
        request: HttpRequest,
        authorization: str = Header(default=""),
    ) -> dict[str, Any]:
        if body.stream:
            raise HTTPException(status_code=422, detail="streaming is not supported")
        if not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="model capability is required")
        token = authorization.removeprefix("Bearer ").strip()
        try:
            capability = tokens.verify(token)
        except ValueError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        if capability.logical_model != body.model:
            raise HTTPException(status_code=403, detail="logical model is outside capability")
        document = body.model_dump(exclude={"model", "messages", "max_tokens", "stream"})
        return await execute(
            InvokeBody(
                capabilityToken=token,
                messages=body.messages,
                maxTokens=body.max_tokens or 4096,
                parameters=document,
            ),
            request,
        )

    return app


async def _reserve(
    database: Database,
    *,
    tenant_id: UUID,
    project_id: UUID,
    run_id: UUID,
    max_tokens: int,
    request_id: str,
) -> None:
    async with tenant_transaction(
        database.sessions, tenant_id=tenant_id, project_id=project_id
    ) as session:
        run = await session.scalar(
            select(Run).where(Run.id == run_id, Run.project_id == project_id).with_for_update()
        )
        if run is None:
            raise LookupError("run not found")
        if await session.scalar(
            select(ModelUsageRecord.id).where(
                ModelUsageRecord.run_id == run_id,
                ModelUsageRecord.request_id == request_id,
            )
        ):
            raise HTTPException(status_code=409, detail="model capability was replayed")
        usage = dict(run.usage)
        reservations = dict(usage.get("modelReservations", {}))
        if request_id in reservations:
            raise HTTPException(status_code=409, detail="model request is already in progress")
        used = int(usage.get("tokens", 0))
        reserved = int(usage.get("reservedTokens", 0))
        if used + reserved + max_tokens > int(run.budgets["maxTokens"]):
            raise HTTPException(status_code=409, detail="BUDGET_EXCEEDED")
        if float(usage.get("costUsd", 0)) >= float(run.budgets["maxCostUsd"]):
            raise HTTPException(status_code=409, detail="BUDGET_EXCEEDED")
        usage["reservedTokens"] = reserved + max_tokens
        reservations[request_id] = max_tokens
        usage["modelReservations"] = reservations
        run.usage = usage


async def _release(
    database: Database,
    *,
    tenant_id: UUID,
    project_id: UUID,
    run_id: UUID,
    reserved: int,
    request_id: str,
) -> None:
    async with tenant_transaction(
        database.sessions, tenant_id=tenant_id, project_id=project_id
    ) as session:
        run = await session.get(Run, run_id, with_for_update=True)
        if run is not None:
            usage = dict(run.usage)
            usage["reservedTokens"] = max(0, int(usage.get("reservedTokens", 0)) - reserved)
            reservations = dict(usage.get("modelReservations", {}))
            reservations.pop(request_id, None)
            usage["modelReservations"] = reservations
            run.usage = usage


async def _commit(
    database: Database,
    *,
    tenant_id: UUID,
    project_id: UUID,
    run_id: UUID,
    capability_jti: str,
    actor_id: str,
    logical_model: str,
    provider_model: str,
    price_version: str,
    reserved: int,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    policy_revision: str,
) -> None:
    async with tenant_transaction(
        database.sessions, tenant_id=tenant_id, project_id=project_id
    ) as session:
        run = await session.get(Run, run_id, with_for_update=True)
        if run is None:
            raise LookupError("run not found")
        if await session.scalar(
            select(ModelUsageRecord.id).where(
                ModelUsageRecord.run_id == run_id,
                ModelUsageRecord.request_id == capability_jti,
            )
        ):
            raise HTTPException(status_code=409, detail="model capability was replayed")
        usage = dict(run.usage)
        usage["reservedTokens"] = max(0, int(usage.get("reservedTokens", 0)) - reserved)
        reservations = dict(usage.get("modelReservations", {}))
        reservations.pop(capability_jti, None)
        usage["modelReservations"] = reservations
        usage["tokens"] = int(usage.get("tokens", 0)) + input_tokens + output_tokens
        usage["costUsd"] = float(usage.get("costUsd", 0)) + cost_usd
        run.usage = usage
        session.add(
            ModelUsageRecord(
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
                request_id=capability_jti,
                logical_model=logical_model,
                provider=provider_model.partition("/")[0],
                provider_model=provider_model,
                price_version=price_version,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd_micros=round(cost_usd * 1_000_000),
                occurred_at=datetime.now(UTC),
            )
        )
        await AuditRepository().append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor_id,
            action="model.invoke",
            resource_type="model",
            resource_id=logical_model,
            run_id=run_id,
            policy_revision=policy_revision,
            metadata={
                "providerModel": provider_model,
                "inputTokens": input_tokens,
                "outputTokens": output_tokens,
                "costUsd": cost_usd,
                "priceVersion": price_version,
            },
        )
        ratio = max(
            usage["tokens"] / int(run.budgets["maxTokens"]),
            usage["costUsd"] / float(run.budgets["maxCostUsd"]),
        )
        event_type = (
            "budget.exhausted" if ratio >= 1 else "budget.warning" if ratio >= 0.8 else None
        )
        if event_type is not None:
            await EventRepository().append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
                transition_id=uuid7(),
                event_type=event_type,
                payload={"tokens": usage["tokens"], "costUsd": usage["costUsd"]},
                occurred_at=datetime.now(UTC),
            )


def _litellm(
    url: str,
    api_key: str,
    model: str,
    body: InvokeBody,
    timeout_seconds: float,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": body.messages,
        "max_tokens": body.max_tokens,
        **body.parameters,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = Request(
        f"{url.rstrip('/')}/v1/chat/completions",
        data=json.dumps(payload, separators=(",", ":")).encode(),
        headers=headers,
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return cast(dict[str, Any], json.loads(response.read(4 * 1024 * 1024)))


def _model_request_id(capability_jti: str, body: InvokeBody) -> str:
    document = body.model_dump(mode="json", by_alias=True, exclude={"capability_token"})
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
    return f"{capability_jti}:{hashlib.sha256(encoded).hexdigest()}"


def run() -> None:
    configure_json_logging()
    settings = Settings()
    telemetry = configure_telemetry(
        "model-gateway", endpoint=settings.otlp_endpoint, enabled=settings.telemetry_enabled
    )
    try:
        uvicorn.run(
            create_app(settings),
            host=settings.model_gateway_host,
            port=settings.model_gateway_port,
            **settings.workload_tls().uvicorn_options(),
        )
    finally:
        telemetry.shutdown()
