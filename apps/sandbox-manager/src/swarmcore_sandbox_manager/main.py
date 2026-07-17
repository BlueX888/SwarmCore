from __future__ import annotations

import asyncio
import ipaddress
import json
import ssl
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import UUID

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi import Request as HttpRequest
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from swarmcore_domain import uuid7
from swarmcore_governance import (
    OpaPolicyEngine,
    PolicyDenied,
    PolicyError,
    PolicyRequest,
    PolicySubject,
    RolePolicyEngine,
    SandboxAdmission,
    SandboxCapabilityIssuer,
    SandboxRequest,
    SandboxViolation,
    WorkloadTls,
)
from swarmcore_observability import (
    SwarmMetrics,
    configure_json_logging,
    configure_telemetry,
    get_tracer,
)
from swarmcore_persistence import AuditRepository, Database, tenant_transaction
from swarmcore_persistence.models import SandboxExecution


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://swarmcore:swarmcore@localhost:5433/swarmcore"
    sandbox_capability_secret: str = "development-only-sandbox-secret-32-bytes"
    sandbox_allowed_images: frozenset[str] = frozenset()
    sandbox_dry_run: bool = True
    sandbox_namespace: str = "swarmcore-sandboxes"
    kubernetes_api: str = "https://kubernetes.default.svc"
    kubernetes_token_file: str = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    kubernetes_ca_file: str = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
    policy_mode: Literal["local", "opa"] = "local"
    opa_decision_url: str = "http://localhost:8181/v1/data/swarmcore/decision"
    sandbox_host: str = "127.0.0.1"
    sandbox_port: int = 8092
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
    def validate_sandbox_boundary(self) -> Settings:
        self.workload_tls().validate(required=self.deployment_mode == "production")
        if self.deployment_mode == "production":
            if self.sandbox_capability_secret.startswith("development-"):
                raise ValueError(
                    "production Sandbox Manager requires a managed capability secret"
                )
            if self.policy_mode != "opa":
                raise ValueError("production Sandbox Manager requires OPA")
        if not self.sandbox_dry_run and not self.sandbox_allowed_images:
            raise ValueError("active Sandbox Manager requires digest-pinned allowlisted images")
        return self


class SandboxBody(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    capability_token: str = Field(alias="capabilityToken")
    image: str
    command: tuple[str, ...]
    cpu_millis: int = Field(alias="cpuMillis")
    memory_mib: int = Field(alias="memoryMiB")
    workspace_mib: int = Field(alias="workspaceMiB")
    timeout_seconds: int = Field(alias="timeoutSeconds")
    network_targets: tuple[str, ...] = Field(default=(), alias="networkTargets")
    privileged: bool = False
    host_paths: tuple[str, ...] = Field(default=(), alias="hostPaths")


class SandboxStatusBody(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    capability_token: str = Field(alias="capabilityToken")


class KubernetesJobClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def submit(
        self, manifest: dict[str, Any], network_policy: dict[str, Any]
    ) -> dict[str, Any]:
        if self._settings.sandbox_dry_run:
            return manifest
        return await asyncio.to_thread(self._submit, manifest, network_policy)

    def _submit(self, manifest: dict[str, Any], network_policy: dict[str, Any]) -> dict[str, Any]:
        token = Path(self._settings.kubernetes_token_file).read_text().strip()
        context = ssl.create_default_context(cafile=self._settings.kubernetes_ca_file)
        network_url = (
            f"{self._settings.kubernetes_api}/apis/networking.k8s.io/v1/namespaces/"
            f"{self._settings.sandbox_namespace}/networkpolicies"
        )
        job_url = (
            f"{self._settings.kubernetes_api}/apis/batch/v1/namespaces/"
            f"{self._settings.sandbox_namespace}/jobs"
        )
        self._post(network_url, network_policy, token, context)
        return self._post(job_url, manifest, token, context)

    async def status(self, execution_id: str) -> dict[str, Any]:
        if self._settings.sandbox_dry_run:
            return {"status": "SUBMITTED", "reason": None, "retryable": False}
        return await asyncio.to_thread(self._status, execution_id)

    def _status(self, execution_id: str) -> dict[str, Any]:
        token = Path(self._settings.kubernetes_token_file).read_text().strip()
        context = ssl.create_default_context(cafile=self._settings.kubernetes_ca_file)
        job_name = quote(f"swarm-{execution_id}", safe="")
        job_url = (
            f"{self._settings.kubernetes_api}/apis/batch/v1/namespaces/"
            f"{self._settings.sandbox_namespace}/jobs/{job_name}"
        )
        selector = quote(f"swarmcore.io/sandbox={execution_id}", safe="")
        pods_url = (
            f"{self._settings.kubernetes_api}/api/v1/namespaces/"
            f"{self._settings.sandbox_namespace}/pods?labelSelector={selector}"
        )
        return _sandbox_status(
            self._get(job_url, token, context),
            self._get(pods_url, token, context),
        )

    @staticmethod
    def _post(
        url: str,
        manifest: dict[str, Any],
        token: str,
        context: ssl.SSLContext,
    ) -> dict[str, Any]:
        request = Request(
            url,
            data=json.dumps(manifest, separators=(",", ":")).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(request, timeout=10, context=context) as response:
            result: dict[str, Any] = json.loads(response.read(1_048_576))
            return result

    @staticmethod
    def _get(url: str, token: str, context: ssl.SSLContext) -> dict[str, Any]:
        request = Request(url, headers={"Authorization": f"Bearer {token}"})
        with urlopen(request, timeout=10, context=context) as response:
            result: dict[str, Any] = json.loads(response.read(1_048_576))
            return result


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or Settings()
    metrics = SwarmMetrics.create("sandbox-manager")
    tokens = SandboxCapabilityIssuer(configured.sandbox_capability_secret.encode())
    admission = SandboxAdmission(allowed_images=configured.sandbox_allowed_images)
    policy = (
        OpaPolicyEngine(configured.opa_decision_url)
        if configured.policy_mode == "opa"
        else RolePolicyEngine()
    )
    kubernetes = KubernetesJobClient(configured)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.database = Database(configured.database_url)
        try:
            yield
        finally:
            await app.state.database.dispose()

    app = FastAPI(title="SwarmCore Sandbox Manager", lifespan=lifespan)

    @app.middleware("http")
    async def trace_sandbox_request(request: HttpRequest, call_next: Any) -> Any:
        with get_tracer("sandbox-manager").start_as_current_span("sandbox.job") as span:
            try:
                response = await call_next(request)
            except Exception as exc:
                span.set_attribute("error.type", type(exc).__name__)
                raise
            for name, attribute in (
                ("tenant_id", "tenant.id"),
                ("project_id", "project.id"),
                ("run_id", "swarm.run.id"),
                ("task_id", "swarm.task.id"),
            ):
                value = getattr(request.state, name, None)
                if value is not None:
                    span.set_attribute(attribute, str(value))
            return response

    @app.post("/internal/v1/sandboxes", status_code=202)
    async def submit(body: SandboxBody, request: HttpRequest) -> dict[str, Any]:
        try:
            capability = tokens.verify(body.capability_token)
            request.state.tenant_id = capability.tenant_id
            request.state.project_id = capability.project_id
            request.state.run_id = capability.run_id
            request.state.task_id = capability.task_execution_id
            sandbox_request = SandboxRequest(
                image=body.image,
                command=body.command,
                cpu_millis=body.cpu_millis,
                memory_mib=body.memory_mib,
                workspace_mib=body.workspace_mib,
                timeout_seconds=body.timeout_seconds,
                network_targets=body.network_targets,
                privileged=body.privileged,
                host_paths=body.host_paths,
            )
            decision = await policy.evaluate(
                PolicyRequest(
                    subject=PolicySubject(
                        id=capability.subject_id,
                        tenantId=capability.tenant_id,
                        roles=("workload",),
                    ),
                    action="sandbox.execute",
                    resource={
                        "projectId": capability.project_id,
                        "image": body.image,
                        "allowedEgress": list(body.network_targets),
                    },
                    context={"runId": capability.run_id},
                )
            )
            job = admission.admit(sandbox_request, decision)
        except (SandboxViolation, PolicyDenied) as exc:
            if isinstance(exc, PolicyDenied):
                metrics.policy_denied.add(1, {"action": "sandbox.execute"})
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except PolicyError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        execution_id = uuid7()
        manifest = _manifest(
            job.request,
            execution_id=str(execution_id),
            namespace=configured.sandbox_namespace,
        )
        submitted = await kubernetes.submit(
            manifest,
            _network_policy(
                job.request,
                execution_id=str(execution_id),
                namespace=configured.sandbox_namespace,
            ),
        )
        tenant_id = UUID(capability.tenant_id)
        project_id = UUID(capability.project_id)
        run_id = UUID(capability.run_id)
        database: Database = request.app.state.database
        async with tenant_transaction(
            database.sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            session.add(
                SandboxExecution(
                    id=execution_id,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    run_id=run_id,
                    task_execution_id=capability.task_execution_id,
                    image_digest=body.image,
                    status="SUBMITTED",
                    policy_revision=decision.policy_revision,
                )
            )
            await AuditRepository().append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id=capability.subject_id,
                action="sandbox.execute",
                resource_type="sandbox_execution",
                resource_id=str(execution_id),
                run_id=run_id,
                policy_revision=decision.policy_revision,
                metadata={"image": body.image},
            )
        return {
            "sandboxExecutionId": str(execution_id),
            "status": "SUBMITTED",
            "jobName": submitted["metadata"]["name"],
        }

    @app.post("/internal/v1/sandboxes/{execution_id}:reconcile")
    async def reconcile(
        execution_id: UUID, body: SandboxStatusBody, request: HttpRequest
    ) -> dict[str, Any]:
        try:
            capability = tokens.verify(body.capability_token)
        except SandboxViolation as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        status = await kubernetes.status(str(execution_id))
        tenant_id = UUID(capability.tenant_id)
        project_id = UUID(capability.project_id)
        database: Database = request.app.state.database
        async with tenant_transaction(
            database.sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            execution = await session.get(SandboxExecution, execution_id, with_for_update=True)
            if (
                execution is None
                or execution.run_id != UUID(capability.run_id)
                or execution.task_execution_id != capability.task_execution_id
            ):
                raise HTTPException(status_code=404, detail="sandbox execution not found")
            execution.status = str(status["status"])
            if execution.status in {"SUCCEEDED", "FAILED", "TIMED_OUT"}:
                execution.cleanup_at = datetime.now(UTC)
            await AuditRepository().append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id=capability.subject_id,
                action="sandbox.reconcile",
                resource_type="sandbox_execution",
                resource_id=str(execution_id),
                run_id=execution.run_id,
                policy_revision=execution.policy_revision,
                metadata={
                    "status": status["status"],
                    "reason": status["reason"],
                    "retryable": status["retryable"],
                },
            )
        return {"sandboxExecutionId": str(execution_id), **status}

    return app


def _manifest(request: SandboxRequest, *, execution_id: str, namespace: str) -> dict[str, Any]:
    return {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {"name": f"swarm-{execution_id}", "namespace": namespace},
        "spec": {
            "ttlSecondsAfterFinished": 300,
            "activeDeadlineSeconds": request.timeout_seconds,
            "backoffLimit": 0,
            "template": {
                "metadata": {"labels": {"swarmcore.io/sandbox": execution_id}},
                "spec": {
                    "runtimeClassName": "gvisor",
                    "restartPolicy": "Never",
                    "automountServiceAccountToken": False,
                    "securityContext": {
                        "runAsNonRoot": True,
                        "seccompProfile": {"type": "RuntimeDefault"},
                    },
                    "containers": [
                        {
                            "name": "sandbox",
                            "image": request.image,
                            "command": list(request.command),
                            "securityContext": {
                                "allowPrivilegeEscalation": False,
                                "readOnlyRootFilesystem": True,
                                "capabilities": {"drop": ["ALL"]},
                            },
                            "resources": {
                                "limits": {
                                    "cpu": f"{request.cpu_millis}m",
                                    "memory": f"{request.memory_mib}Mi",
                                    "ephemeral-storage": f"{request.workspace_mib}Mi",
                                }
                            },
                        }
                    ],
                },
            },
        },
    }


def _network_policy(
    request: SandboxRequest, *, execution_id: str, namespace: str
) -> dict[str, Any]:
    egress: list[dict[str, Any]] = []
    for target in request.network_targets:
        host, raw_port = target.rsplit(":", 1)
        address = ipaddress.ip_address(host.removeprefix("[").removesuffix("]"))
        prefix = 32 if address.version == 4 else 128
        egress.append(
            {
                "to": [{"ipBlock": {"cidr": f"{address}/{prefix}"}}],
                "ports": [{"protocol": "TCP", "port": int(raw_port)}],
            }
        )
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {"name": f"swarm-{execution_id}", "namespace": namespace},
        "spec": {
            "podSelector": {"matchLabels": {"swarmcore.io/sandbox": execution_id}},
            "policyTypes": ["Ingress", "Egress"],
            "ingress": [],
            "egress": egress,
        },
    }


def _sandbox_status(job: dict[str, Any], pods: dict[str, Any]) -> dict[str, Any]:
    raw_status = job.get("status")
    status: dict[str, Any] = raw_status if isinstance(raw_status, dict) else {}
    raw_conditions = status.get("conditions")
    conditions: list[Any] = raw_conditions if isinstance(raw_conditions, list) else []
    for condition in conditions:
        if not isinstance(condition, dict) or condition.get("status") != "True":
            continue
        if condition.get("type") == "Complete":
            return {"status": "SUCCEEDED", "reason": None, "retryable": False}
        if condition.get("type") == "Failed":
            reason = str(condition.get("reason") or "JobFailed")
            return {
                "status": "TIMED_OUT" if reason == "DeadlineExceeded" else "FAILED",
                "reason": reason,
                "retryable": reason in {"NodeLost", "Evicted", "Shutdown"},
            }
    raw_items = pods.get("items")
    items: list[Any] = raw_items if isinstance(raw_items, list) else []
    for pod in items:
        if not isinstance(pod, dict):
            continue
        raw_pod_status = pod.get("status")
        pod_status: dict[str, Any] = raw_pod_status if isinstance(raw_pod_status, dict) else {}
        reason = str(pod_status.get("reason") or "")
        if reason in {"NodeLost", "Evicted", "Shutdown"}:
            return {"status": "FAILED", "reason": reason, "retryable": True}
    if int(status.get("active", 0) or 0) > 0:
        return {"status": "RUNNING", "reason": None, "retryable": False}
    return {"status": "SUBMITTED", "reason": None, "retryable": False}


def run() -> None:
    configure_json_logging()
    settings = Settings()
    telemetry = configure_telemetry(
        "sandbox-manager", endpoint=settings.otlp_endpoint, enabled=settings.telemetry_enabled
    )
    try:
        uvicorn.run(
            create_app(settings),
            host=settings.sandbox_host,
            port=settings.sandbox_port,
            **settings.workload_tls().uvicorn_options(),
        )
    finally:
        telemetry.shutdown()
