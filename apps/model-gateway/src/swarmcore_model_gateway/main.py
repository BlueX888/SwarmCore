from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, Any, Literal, cast
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
from uuid import UUID

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi import Request as HttpRequest
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import select
from swarmcore_domain import uuid7
from swarmcore_governance import (
    ModelCapabilityIssuer,
    OpaPolicyEngine,
    PolicyRequest,
    PolicySubject,
    RolePolicyEngine,
    SecretError,
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
from swarmcore_persistence.models import ModelUsageRecord, ProjectConfiguration, Run


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://swarmcore:swarmcore@localhost:5433/swarmcore"
    model_capability_secret: str = "development-model-capability-secret-32-bytes"
    model_routes: dict[str, str] = {
        "model://general": "openai/gpt-4o-mini",
        "model://deepseek-v4-flash": "DeepSeek-V4-Flash",
        "model://deepseek-v4-pro": "DeepSeek-V4-Pro",
        "model://kimi-k2.5": "kimi-k2.5",
        "model://kimi-k2.7-code": "kimi-k2.7-code",
    }
    model_price_version: str = "local-price:v1"
    litellm_url: str = "http://localhost:4000"
    litellm_timeout_seconds: float = 300
    litellm_secret_ref: str = "secret://platform/litellm"
    model_provider_url: str = ""
    model_provider_api_key: str = ""
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
            if self.model_provider_url or self.model_provider_api_key:
                raise ValueError(
                    "production Model Gateway requires provider credentials from Vault"
                )
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


class ModelProviderConfigurationBody(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    logical_model: str = Field(alias="logicalModel", min_length=1, max_length=512)
    provider_url: AnyHttpUrl = Field(alias="providerUrl")
    model_name: str = Field(alias="modelName", min_length=1, max_length=256)
    api_key: str | None = Field(default=None, alias="apiKey", max_length=8192)


TenantHeader = Annotated[UUID, Header(alias="X-Tenant-ID")]


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
        runtime_provider = await _runtime_provider_configuration(
            database,
            secrets,
            tenant_id=tenant_id,
            project_id=project_id,
            logical_model=capability.logical_model,
        )
        provider_url = runtime_provider[0] if runtime_provider else configured.model_provider_url
        provider_api_key = (
            runtime_provider[1] if runtime_provider else configured.model_provider_api_key
        )
        if runtime_provider:
            provider_model = runtime_provider[2]
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
            if provider_url:
                result = await asyncio.to_thread(
                    _litellm,
                    _provider_root(provider_url),
                    provider_api_key,
                    provider_model,
                    body.model_copy(
                        update={
                            "messages": _provider_compatible_messages(body.messages),
                            "parameters": _provider_compatible_parameters(body.parameters),
                        }
                    ),
                    configured.litellm_timeout_seconds,
                )
            elif secrets is None:
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
        except Exception as exc:
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
            if isinstance(exc, HTTPException):
                raise
            raise HTTPException(
                status_code=502, detail=f"model provider failed: {exc}"
            ) from exc
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

    @app.get("/internal/v1/readiness")
    async def readiness() -> dict[str, Any]:
        if not configured.model_routes:
            return {"models": []}
        secret_available = (
            bool(configured.model_provider_api_key)
            if configured.model_provider_url
            else secrets is None
        )
        health_api_key = ""
        if secrets is not None and not configured.model_provider_url:
            try:
                async with secrets.lease(configured.litellm_secret_ref) as lease:
                    leased_api_key = lease.values.get("apiKey")
                    secret_available = isinstance(leased_api_key, str) and bool(leased_api_key)
                    health_api_key = leased_api_key if isinstance(leased_api_key, str) else ""
            except Exception:
                secret_available = False
        endpoint_url = (
            _provider_root(configured.model_provider_url)
            if configured.model_provider_url
            else configured.litellm_url
        )
        endpoint_api_key = (
            configured.model_provider_api_key
            if configured.model_provider_url
            else health_api_key
        )
        endpoint_healthy = await asyncio.to_thread(
            _probe_litellm,
            endpoint_url,
            configured.litellm_timeout_seconds,
            endpoint_api_key,
        )
        return {
            "models": [
                {
                    "logicalModel": logical_model,
                    "providerModel": provider_model,
                    "routeRegistered": True,
                    "secretAvailable": secret_available,
                    "endpointHealthy": endpoint_healthy,
                }
                for logical_model, provider_model in sorted(configured.model_routes.items())
            ]
        }

    @app.get("/internal/v1/projects/{project_id}/model-provider")
    async def get_model_provider(
        project_id: UUID,
        request: HttpRequest,
        logical_model: str,
        x_tenant_id: TenantHeader,
    ) -> dict[str, Any]:
        database: Database = request.app.state.database
        saved = await _saved_runtime_provider(
            database, tenant_id=x_tenant_id, project_id=project_id, logical_model=logical_model
        )
        if saved is None:
            return {
                "logicalModel": logical_model,
                "providerUrl": "",
                "modelName": configured.model_routes.get(logical_model, ""),
                "apiKeyConfigured": False,
            }
        return {
            "logicalModel": logical_model,
            "providerUrl": saved[0],
            "modelName": saved[1],
            "apiKeyConfigured": bool(saved[2]),
        }

    @app.put("/internal/v1/projects/{project_id}/model-provider")
    async def put_model_provider(
        project_id: UUID,
        body: ModelProviderConfigurationBody,
        request: HttpRequest,
        x_tenant_id: TenantHeader,
    ) -> dict[str, Any]:
        if body.api_key and (not configured.vault_token or secrets is None):
            raise HTTPException(status_code=503, detail="Vault is required to store the API key")
        database: Database = request.app.state.database
        secret_ref = _model_secret_ref(x_tenant_id, project_id, body.logical_model)
        existing = await _saved_runtime_provider(
            database,
            tenant_id=x_tenant_id,
            project_id=project_id,
            logical_model=body.logical_model,
        )
        if body.api_key:
            await asyncio.to_thread(
                _vault_write_api_key,
                configured.vault_address,
                configured.vault_token,
                secret_ref,
                body.api_key,
                configured.litellm_timeout_seconds,
            )
        elif existing is None or not existing[2]:
            raise HTTPException(status_code=422, detail="API key is required")
        async with tenant_transaction(
            database.sessions, tenant_id=x_tenant_id, project_id=project_id
        ) as session:
            name = _model_runtime_name(body.logical_model)
            saved = await session.scalar(
                select(ProjectConfiguration).where(
                    ProjectConfiguration.tenant_id == x_tenant_id,
                    ProjectConfiguration.project_id == project_id,
                    ProjectConfiguration.kind == "model",
                    ProjectConfiguration.name == name,
                )
            )
            document = {
                "providerUrl": str(body.provider_url).rstrip("/"),
                "modelName": body.model_name.strip(),
                "secretRef": secret_ref,
            }
            if saved is None:
                session.add(ProjectConfiguration(
                    tenant_id=x_tenant_id, project_id=project_id, kind="model", name=name,
                    source_ref=body.logical_model, configuration=document,
                    created_by="model-provider-ui", updated_by="model-provider-ui",
                ))
            else:
                saved.source_ref = body.logical_model
                saved.configuration = document
                saved.revision += 1
                saved.updated_by = "model-provider-ui"
        return {
            "logicalModel": body.logical_model,
            "providerUrl": str(body.provider_url).rstrip("/"),
            "modelName": body.model_name.strip(),
            "apiKeyConfigured": True,
        }

    @app.post("/internal/v1/projects/{project_id}/model-provider:test")
    async def test_model_provider(
        project_id: UUID,
        body: ModelProviderConfigurationBody,
        request: HttpRequest,
        x_tenant_id: TenantHeader,
    ) -> dict[str, Any]:
        api_key = body.api_key or ""
        if not api_key:
            runtime = await _runtime_provider_configuration(
                request.app.state.database,
                secrets,
                tenant_id=x_tenant_id,
                project_id=project_id,
                logical_model=body.logical_model,
            )
            if runtime is not None:
                api_key = runtime[1]
        if not api_key:
            raise HTTPException(status_code=422, detail="API key is required")
        probe = InvokeBody(
            capabilityToken="probe",
            messages=[{"role": "user", "content": "Reply with OK only."}],
            maxTokens=16,
            parameters={"temperature": 0},
        )
        started = asyncio.get_running_loop().time()
        try:
            result = await asyncio.to_thread(
                _litellm,
                _provider_root(str(body.provider_url)),
                api_key,
                body.model_name,
                probe,
                min(configured.litellm_timeout_seconds, 30),
            )
            choices = result.get("choices")
            if not isinstance(choices, list) or not choices:
                raise ValueError("provider returned no model choices")
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"model connection failed: {exc}") from exc
        return {
            "connected": True,
            "modelName": body.model_name,
            "latencyMs": round((asyncio.get_running_loop().time() - started) * 1000),
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


def _is_portal_capability_invoke_url(url: str) -> bool:
    normalized = url.rstrip("/")
    return "/openapi/capabilities/" in normalized and normalized.endswith("/invoke")


def _portal_health_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "/api/v1/health", "", ""))


def _probe_litellm(url: str, timeout_seconds: float, api_key: str = "") -> bool:
    timeout = min(timeout_seconds, 5.0)
    probes: tuple[Request, ...]
    if _is_portal_capability_invoke_url(url):
        probes = (
            Request(
                _portal_health_url(url),
                headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
                method="GET",
            ),
        )
    else:
        probes = (
            Request(f"{url.rstrip('/')}/health/liveliness", method="GET"),
            Request(
                f"{url.rstrip('/')}/v1/models",
                headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
                method="GET",
            ),
        )
    for request in probes:
        try:
            with urlopen(request, timeout=timeout) as response:
                status = int(response.status)
                if 200 <= status < 300:
                    return True
        except Exception:
            continue
    return False


def _provider_root(url: str) -> str:
    normalized = url.rstrip("/")
    if _is_portal_capability_invoke_url(normalized):
        return normalized
    return normalized[:-3] if normalized.endswith("/v1") else normalized


def _model_runtime_name(logical_model: str) -> str:
    return f"__runtime_provider__:{logical_model.rsplit('@', 1)[0]}"


def _model_secret_ref(tenant_id: UUID, project_id: UUID, logical_model: str) -> str:
    digest = hashlib.sha256(logical_model.encode()).hexdigest()[:16]
    return f"secret://projects/{tenant_id}/{project_id}/models/{digest}"


async def _saved_runtime_provider(
    database: Database,
    *,
    tenant_id: UUID,
    project_id: UUID,
    logical_model: str,
) -> tuple[str, str, str] | None:
    async with tenant_transaction(
        database.sessions, tenant_id=tenant_id, project_id=project_id
    ) as session:
        saved = await session.scalar(
            select(ProjectConfiguration).where(
                ProjectConfiguration.tenant_id == tenant_id,
                ProjectConfiguration.project_id == project_id,
                ProjectConfiguration.kind == "model",
                ProjectConfiguration.name == _model_runtime_name(logical_model),
            )
        )
        if saved is None:
            return None
        document = saved.configuration
        return (
            str(document.get("providerUrl", "")),
            str(document.get("modelName", "")),
            str(document.get("secretRef", "")),
        )


async def _runtime_provider_configuration(
    database: Database,
    secrets: VaultSecretProvider | None,
    *,
    tenant_id: UUID,
    project_id: UUID,
    logical_model: str,
) -> tuple[str, str, str] | None:
    saved = await _saved_runtime_provider(
        database, tenant_id=tenant_id, project_id=project_id, logical_model=logical_model
    )
    if saved is None:
        return None
    provider_url, model_name, secret_ref = saved
    if not provider_url or not model_name or not secret_ref or secrets is None:
        return None
    try:
        async with secrets.lease(secret_ref) as lease:
            api_key = lease.values.get("apiKey", "")
    except SecretError:
        # Prefer the env/direct provider over a broken project Vault binding.
        return None
    if not api_key:
        return None
    return provider_url, api_key, model_name


def _vault_write_api_key(
    address: str,
    token: str,
    secret_ref: str,
    api_key: str,
    timeout_seconds: float,
) -> None:
    path = secret_ref.removeprefix("secret://")
    request = Request(
        f"{address.rstrip('/')}/v1/secret/data/{path}",
        data=json.dumps({"data": {"apiKey": api_key}}).encode(),
        headers={"Content-Type": "application/json", "X-Vault-Token": token},
        method="POST",
    )
    with urlopen(request, timeout=min(timeout_seconds, 10)) as response:
        if not 200 <= int(response.status) < 300:
            raise RuntimeError("Vault rejected the API key")


def _provider_compatible_messages(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {**message, "role": "system"} if message.get("role") == "developer" else message
        for message in messages
    ]


def _provider_compatible_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(parameters)
    response_format = normalized.get("response_format")
    if isinstance(response_format, dict) and response_format.get("type") not in {
        "text",
        "json_object",
        "json_schema",
    }:
        normalized["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "structured_output",
                "strict": True,
                "schema": response_format,
            },
        }
    return normalized


def _litellm(
    url: str,
    api_key: str,
    model: str,
    body: InvokeBody,
    timeout_seconds: float,
) -> dict[str, Any]:
    if _is_portal_capability_invoke_url(url):
        return _portal_capability_invoke(url, api_key, model, body, timeout_seconds)
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
        return _decode_openai_response(response.read(4 * 1024 * 1024))


def _portal_capability_invoke(
    url: str,
    api_key: str,
    model: str,
    body: InvokeBody,
    timeout_seconds: float,
) -> dict[str, Any]:
    payload = {
        "input": {"messages": body.messages},
        "stream": False,
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = Request(
        url.rstrip("/"),
        data=json.dumps(payload, separators=(",", ":")).encode(),
        headers=headers,
        method="POST",
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return _decode_portal_response(response.read(4 * 1024 * 1024), fallback_model=model)


def _decode_portal_response(raw: bytes, *, fallback_model: str) -> dict[str, Any]:
    document = cast(dict[str, Any], json.loads(raw))
    code = document.get("code")
    if code is not None and int(code) != 200:
        raise ValueError(f"portal capability invoke failed: {document.get('msg', code)}")
    data = cast(dict[str, Any], document.get("data") or {})
    output = cast(dict[str, Any], data.get("output") or {})
    message = cast(dict[str, Any], output.get("message") or {})
    usage_raw = cast(dict[str, Any], data.get("usage") or {})
    trace = cast(dict[str, Any], data.get("trace") or {})
    content = message.get("content")
    assistant: dict[str, Any] = {
        "role": message.get("role") or "assistant",
        "content": content if isinstance(content, str) else "",
    }
    reasoning = message.get("reasoning_content")
    if isinstance(reasoning, str) and reasoning:
        assistant["reasoning_content"] = reasoning
    input_tokens = int(usage_raw.get("inputTokens", 0) or 0)
    output_tokens = int(usage_raw.get("outputTokens", 0) or 0)
    return {
        "id": trace.get("requestId"),
        "object": "chat.completion",
        "model": output.get("model") or fallback_model,
        "choices": [
            {
                "index": 0,
                "message": assistant,
                "finish_reason": output.get("finishReason"),
            }
        ],
        "usage": {
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
        },
        "response_cost": float(usage_raw.get("cost", 0) or 0),
    }


def _decode_openai_response(raw: bytes) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], json.loads(raw))
    except json.JSONDecodeError:
        pass

    chunks: list[dict[str, Any]] = []
    for line in raw.decode("utf-8").splitlines():
        if not line.startswith("data:"):
            continue
        data = line.removeprefix("data:").strip()
        if not data or data == "[DONE]":
            continue
        value = json.loads(data)
        if isinstance(value, dict):
            chunks.append(value)
    if not chunks:
        raise ValueError("model provider returned neither JSON nor OpenAI-compatible SSE")

    messages: dict[int, dict[str, Any]] = {}
    finish_reasons: dict[int, Any] = {}
    usage: dict[str, Any] = {}
    for chunk in chunks:
        if isinstance(chunk.get("usage"), dict):
            usage = cast(dict[str, Any], chunk["usage"])
        for choice in chunk.get("choices", []):
            if not isinstance(choice, dict):
                continue
            index = int(choice.get("index", 0))
            message = messages.setdefault(
                index,
                {"role": "assistant", "content": "", "reasoning_content": ""},
            )
            delta = choice.get("delta")
            if isinstance(delta, dict):
                if isinstance(delta.get("role"), str):
                    message["role"] = delta["role"]
                for field in ("content", "reasoning_content"):
                    if isinstance(delta.get(field), str):
                        message[field] += delta[field]
            if choice.get("finish_reason") is not None:
                finish_reasons[index] = choice["finish_reason"]

    choices = []
    for index, message in sorted(messages.items()):
        if not message["reasoning_content"]:
            message.pop("reasoning_content")
        choices.append(
            {
                "index": index,
                "message": message,
                "finish_reason": finish_reasons.get(index),
            }
        )
    if not choices:
        raise ValueError("model provider SSE contained no choices")
    last = chunks[-1]
    return {
        "id": last.get("id"),
        "object": "chat.completion",
        "created": last.get("created"),
        "model": last.get("model"),
        "choices": choices,
        "usage": usage,
    }


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
