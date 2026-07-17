from __future__ import annotations

import base64
import hashlib
import importlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import func, select
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from swarmcore_governance import (
    ArtifactCapabilityIssuer,
    ArtifactError,
    ArtifactGateway,
    BlobCapabilityIssuer,
    ClamAvScanner,
    InMemoryAuditWriter,
    LocalArtifactStore,
    OpaPolicyEngine,
    PolicyDenied,
    PolicyError,
    PolicyRequest,
    PolicySubject,
    RolePolicyEngine,
    S3ArtifactStore,
    WorkloadTls,
)
from swarmcore_observability import (
    SwarmMetrics,
    configure_json_logging,
    configure_telemetry,
    get_tracer,
)
from swarmcore_persistence import AuditRepository, Database, tenant_transaction
from swarmcore_persistence.models import Artifact, BlobObject, Run


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://swarmcore:swarmcore@localhost:5433/swarmcore"
    artifact_capability_secret: str = "development-artifact-capability-secret-32-bytes"
    artifact_store: Literal["local", "s3"] = "local"
    artifact_root: str = ".tmp/artifacts"
    artifact_s3_bucket: str = ""
    artifact_s3_endpoint: str | None = None
    artifact_s3_region: str = "us-east-1"
    artifact_s3_kms_key_id: str = ""
    artifact_clamav_host: str | None = None
    artifact_max_bytes: int = 100 * 1024 * 1024
    artifact_run_max_bytes: int = 1024 * 1024 * 1024
    policy_mode: Literal["local", "opa"] = "local"
    opa_decision_url: str = "http://localhost:8181/v1/data/swarmcore/decision"
    artifact_gateway_host: str = "127.0.0.1"
    artifact_gateway_port: int = 8091
    cors_origins: tuple[str, ...] = ()
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
    def validate_production_store(self) -> Settings:
        self.workload_tls().validate(required=self.deployment_mode == "production")
        if self.deployment_mode == "production":
            if self.artifact_capability_secret.startswith("development-"):
                raise ValueError(
                    "production Artifact Gateway requires a managed capability secret"
                )
            if self.policy_mode != "opa":
                raise ValueError("production Artifact Gateway requires OPA")
        if self.artifact_store == "s3" and not self.artifact_s3_bucket:
            raise ValueError("S3 artifact store requires a bucket")
        if self.artifact_store == "s3" and self.policy_mode == "opa":
            if not self.artifact_s3_kms_key_id:
                raise ValueError("production S3 artifact store requires a KMS key")
            if not self.artifact_clamav_host:
                raise ValueError("production S3 artifact store requires malware scanning")
        return self


class UploadBody(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    capability_token: str = Field(alias="capabilityToken")
    filename: str
    media_type: str = Field(alias="mediaType")
    kind: str
    content_base64: str = Field(alias="contentBase64")
    data_classification: str = Field(default="internal", alias="dataClassification")
    retention_days: int = Field(default=30, alias="retentionDays", ge=1, le=3650)


class BlobUploadBody(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    capability_token: str = Field(alias="capabilityToken")
    content_base64: str = Field(alias="contentBase64")


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or Settings()
    metrics = SwarmMetrics.create("artifact-gateway")
    tokens = ArtifactCapabilityIssuer(configured.artifact_capability_secret.encode())
    blob_tokens = BlobCapabilityIssuer(configured.artifact_capability_secret.encode())
    store = _store(configured)
    policy = (
        OpaPolicyEngine(configured.opa_decision_url)
        if configured.policy_mode == "opa"
        else RolePolicyEngine()
    )
    content_scanner = (
        ClamAvScanner(configured.artifact_clamav_host)
        if configured.artifact_clamav_host
        else None
    )
    gateway = ArtifactGateway(
        store,
        policy,
        InMemoryAuditWriter(),
        configured.artifact_capability_secret.encode(),
        content_scanner=content_scanner,
        max_artifact_bytes=configured.artifact_max_bytes,
        max_run_bytes=configured.artifact_run_max_bytes,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.database = Database(configured.database_url)
        try:
            yield
        finally:
            await app.state.database.dispose()

    app = FastAPI(title="SwarmCore Artifact Gateway", lifespan=lifespan)
    if configured.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(configured.cors_origins),
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type"],
        )

    @app.middleware("http")
    async def trace_artifact_request(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        with get_tracer("artifact-gateway").start_as_current_span("artifact.request") as span:
            try:
                response = await call_next(request)
            except Exception as exc:
                span.set_attribute("error.type", type(exc).__name__)
                raise
            for name, attribute in (
                ("tenant_id", "tenant.id"),
                ("project_id", "project.id"),
                ("run_id", "swarm.run.id"),
                ("artifact_id", "artifact.id"),
            ):
                value = getattr(request.state, name, None)
                if value is not None:
                    span.set_attribute(attribute, str(value))
            span.set_attribute("http.response.status_code", response.status_code)
            return response

    @app.post("/internal/v1/artifacts", status_code=201)
    async def upload(body: UploadBody, request: Request) -> dict[str, Any]:
        reserved = False
        try:
            capability = tokens.verify(body.capability_token)
            _set_trace_scope(request, capability)
            if capability.action != "artifact.write" or capability.artifact_id is None:
                raise ArtifactError("artifact capability does not allow upload")
            content = base64.b64decode(body.content_base64, validate=True)
            if not content or len(content) > configured.artifact_max_bytes:
                raise ArtifactError("artifact size is outside the allowed range")
            policy_request = _policy_request(capability, "artifact.write")
            decision = (await policy.evaluate(policy_request)).enforce()
            tenant_id = UUID(capability.tenant_id)
            project_id = UUID(capability.project_id)
            run_id = UUID(capability.run_id)
            artifact_id = UUID(capability.artifact_id)
            object_key = (
                f"{capability.tenant_id}/{capability.project_id}/"
                f"{capability.run_id}/{artifact_id}/v1"
            )
            database: Database = request.app.state.database
            await _reserve_upload(
                database,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
                artifact_id=artifact_id,
                object_key=object_key,
                body=body,
                content=content,
                run_limit=configured.artifact_run_max_bytes,
            )
            reserved = True
            ref = await gateway.upload(
                policy_request,
                run_id=capability.run_id,
                filename=body.filename,
                media_type=body.media_type,
                kind=body.kind,
                content=content,
                artifact_id=capability.artifact_id,
            )
        except HTTPException:
            raise
        except PolicyDenied as exc:
            if reserved:
                await _mark_upload_failed(
                    database,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    artifact_id=artifact_id,
                )
            metrics.policy_denied.add(1, {"action": "artifact.write"})
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except PolicyError as exc:
            if reserved:
                await _mark_upload_failed(
                    database,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    artifact_id=artifact_id,
                )
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            if reserved:
                await _mark_upload_failed(
                    database,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    artifact_id=artifact_id,
                )
            status = 403 if isinstance(exc, ArtifactError | ValueError) else 503
            raise HTTPException(status_code=status, detail=str(exc)) from exc
        async with tenant_transaction(
            database.sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            artifact = await session.get(Artifact, artifact_id, with_for_update=True)
            if artifact is None or artifact.status != "UPLOADING":
                raise HTTPException(status_code=409, detail="artifact upload reservation was lost")
            artifact.filename = ref.filename
            artifact.media_type = ref.media_type
            artifact.size_bytes = ref.size_bytes
            artifact.sha256 = ref.sha256
            artifact.status = ref.status
            await AuditRepository().append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id=capability.subject_id,
                action="artifact.upload",
                resource_type="artifact",
                resource_id=ref.id,
                run_id=run_id,
                policy_revision=decision.policy_revision,
                metadata={"sha256": ref.sha256, "sizeBytes": ref.size_bytes},
            )
        return {"artifactId": ref.id, "status": ref.status, "sha256": ref.sha256}

    @app.post("/internal/v1/blobs/{blob_id}")
    async def upload_blob(blob_id: UUID, body: BlobUploadBody, request: Request) -> dict[str, Any]:
        try:
            capability = blob_tokens.verify(body.capability_token)
            if capability.action != "blob.write" or capability.blob_id != str(blob_id):
                raise ArtifactError("blob capability does not allow upload")
            request.state.tenant_id = capability.tenant_id
            request.state.project_id = capability.project_id
            request.state.blob_id = capability.blob_id
            content = base64.b64decode(body.content_base64, validate=True)
            if not content or len(content) > configured.artifact_max_bytes:
                raise ArtifactError("blob size is outside the allowed range")
            decision = (
                await policy.evaluate(_blob_policy_request(capability, "blob.write"))
            ).enforce()
            tenant_id = UUID(capability.tenant_id)
            project_id = UUID(capability.project_id)
            database: Database = request.app.state.database
            async with tenant_transaction(
                database.sessions, tenant_id=tenant_id, project_id=project_id
            ) as session:
                blob = await session.get(BlobObject, blob_id, with_for_update=True)
                if blob is None or blob.project_id != project_id:
                    raise HTTPException(status_code=404, detail="blob not found")
                if blob.status == "AVAILABLE":
                    if hashlib.sha256(content).hexdigest() != blob.sha256:
                        raise HTTPException(status_code=409, detail="blob content differs")
                    return {"blobId": str(blob.id), "status": blob.status, "sha256": blob.sha256}
                if blob.status != "PENDING":
                    raise HTTPException(status_code=409, detail="blob upload is not pending")
                digest = hashlib.sha256(content).hexdigest()
                if len(content) != blob.size_bytes or digest != blob.sha256:
                    blob.status = "REJECTED"
                    blob.scan_status = "HASH_MISMATCH"
                    raise HTTPException(status_code=422, detail="blob size or SHA-256 differs")
                blob.status = "SCANNING"
            try:
                if content_scanner is not None:
                    await content_scanner.scan(content)
                await store.put(blob.object_key, content)
            except Exception:
                await _mark_blob_rejected(
                    database,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    blob_id=blob_id,
                )
                raise
            async with tenant_transaction(
                database.sessions, tenant_id=tenant_id, project_id=project_id
            ) as session:
                blob = await session.get(BlobObject, blob_id, with_for_update=True)
                if blob is None or blob.status != "SCANNING":
                    raise HTTPException(status_code=409, detail="blob upload reservation was lost")
                blob.status = "AVAILABLE"
                blob.scan_status = "CLEAN"
                await AuditRepository().append(
                    session,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    actor_id=capability.subject_id,
                    action="blob.upload",
                    resource_type="blob_object",
                    resource_id=str(blob.id),
                    policy_revision=decision.policy_revision,
                    metadata={"sha256": blob.sha256, "sizeBytes": blob.size_bytes},
                )
            return {"blobId": str(blob_id), "status": "AVAILABLE", "sha256": digest}
        except HTTPException:
            raise
        except (ArtifactError, PolicyDenied, ValueError) as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except PolicyError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/internal/v1/blobs/{blob_id}/content")
    async def read_blob(blob_id: UUID, capability_token: str, request: Request) -> Response:
        try:
            capability = blob_tokens.verify(capability_token)
            if capability.action != "blob.read" or capability.blob_id != str(blob_id):
                raise ArtifactError("blob capability does not allow read")
            decision = (
                await policy.evaluate(_blob_policy_request(capability, "blob.read"))
            ).enforce()
        except (ArtifactError, PolicyDenied) as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except PolicyError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        tenant_id = UUID(capability.tenant_id)
        project_id = UUID(capability.project_id)
        database: Database = request.app.state.database
        async with tenant_transaction(
            database.sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            blob = await session.scalar(
                select(BlobObject).where(
                    BlobObject.id == blob_id,
                    BlobObject.tenant_id == tenant_id,
                    BlobObject.project_id == project_id,
                    BlobObject.status == "AVAILABLE",
                    BlobObject.scan_status == "CLEAN",
                    BlobObject.retention_until > datetime.now(UTC),
                )
            )
            if blob is None:
                raise HTTPException(status_code=404, detail="blob not found")
            content = await store.get(blob.object_key)
            if hashlib.sha256(content).hexdigest() != blob.sha256:
                raise HTTPException(status_code=500, detail="blob integrity check failed")
            await AuditRepository().append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id=capability.subject_id,
                action="blob.read",
                resource_type="blob_object",
                resource_id=str(blob.id),
                policy_revision=decision.policy_revision,
            )
        return Response(content=content, media_type=blob.media_type)

    @app.post("/internal/v1/artifacts/{artifact_id}:read")
    async def read_artifact(artifact_id: UUID, capability_token: str, request: Request) -> Response:
        try:
            capability = tokens.verify(capability_token)
            _set_trace_scope(request, capability)
            if capability.action != "artifact.read" or capability.artifact_id != str(artifact_id):
                raise ArtifactError("artifact capability does not allow read")
            decision = (
                await policy.evaluate(_policy_request(capability, "artifact.read"))
            ).enforce()
        except (ArtifactError, PolicyDenied) as exc:
            if isinstance(exc, PolicyDenied):
                metrics.policy_denied.add(1, {"action": "artifact.read"})
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except PolicyError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        tenant_id = UUID(capability.tenant_id)
        project_id = UUID(capability.project_id)
        database: Database = request.app.state.database
        async with tenant_transaction(
            database.sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            artifact = await session.scalar(
                select(Artifact).where(
                    Artifact.id == artifact_id,
                    Artifact.tenant_id == tenant_id,
                    Artifact.project_id == project_id,
                    Artifact.run_id == UUID(capability.run_id),
                    Artifact.status == "AVAILABLE",
                    (
                        Artifact.retention_until.is_(None)
                        | (Artifact.retention_until > datetime.now(UTC))
                    ),
                )
            )
            if artifact is None:
                raise HTTPException(status_code=404, detail="artifact not found")
            content = await store.get(artifact.object_key)
            if hashlib.sha256(content).hexdigest() != artifact.sha256:
                raise HTTPException(status_code=500, detail="artifact integrity check failed")
            await AuditRepository().append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id=capability.subject_id,
                action="artifact.read",
                resource_type="artifact",
                resource_id=str(artifact.id),
                run_id=artifact.run_id,
                policy_revision=decision.policy_revision,
            )
        return Response(content=content, media_type=artifact.media_type)

    return app


async def _reserve_upload(
    database: Database,
    *,
    tenant_id: UUID,
    project_id: UUID,
    run_id: UUID,
    artifact_id: UUID,
    object_key: str,
    body: UploadBody,
    content: bytes,
    run_limit: int,
) -> None:
    async with tenant_transaction(
        database.sessions, tenant_id=tenant_id, project_id=project_id
    ) as session:
        run = await session.scalar(
            select(Run)
            .where(
                Run.id == run_id,
                Run.tenant_id == tenant_id,
                Run.project_id == project_id,
            )
            .with_for_update()
        )
        if run is None:
            raise HTTPException(status_code=404, detail="run not found")
        if await session.get(Artifact, artifact_id) is not None:
            raise HTTPException(status_code=409, detail="artifact capability was replayed")
        used = await session.scalar(
            select(func.coalesce(func.sum(Artifact.size_bytes), 0)).where(
                Artifact.run_id == run_id,
                Artifact.tenant_id == tenant_id,
                Artifact.status.in_(("UPLOADING", "SCANNING", "AVAILABLE")),
            )
        )
        if int(used or 0) + len(content) > run_limit:
            raise HTTPException(status_code=409, detail="run artifact quota would be exceeded")
        session.add(
            Artifact(
                id=artifact_id,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
                kind=body.kind,
                filename=body.filename,
                media_type=body.media_type,
                object_key=object_key,
                size_bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                status="UPLOADING",
                data_classification=body.data_classification,
                retention_until=datetime.now(UTC) + timedelta(days=body.retention_days),
            )
        )


async def _mark_upload_failed(
    database: Database,
    *,
    tenant_id: UUID,
    project_id: UUID,
    artifact_id: UUID,
) -> None:
    async with tenant_transaction(
        database.sessions, tenant_id=tenant_id, project_id=project_id
    ) as session:
        artifact = await session.get(Artifact, artifact_id, with_for_update=True)
        if artifact is not None and artifact.status == "UPLOADING":
            artifact.status = "REJECTED"


async def _mark_blob_rejected(
    database: Database,
    *,
    tenant_id: UUID,
    project_id: UUID,
    blob_id: UUID,
) -> None:
    async with tenant_transaction(
        database.sessions, tenant_id=tenant_id, project_id=project_id
    ) as session:
        blob = await session.get(BlobObject, blob_id, with_for_update=True)
        if blob is not None and blob.status == "SCANNING":
            blob.status = "REJECTED"
            blob.scan_status = "REJECTED"


def _store(settings: Settings) -> Any:
    if settings.artifact_store == "local":
        return LocalArtifactStore(Path(settings.artifact_root))
    if settings.artifact_store != "s3":
        raise ValueError("artifact store configuration is invalid")
    boto3 = importlib.import_module("boto3")
    client = boto3.client(
        "s3",
        endpoint_url=settings.artifact_s3_endpoint,
        region_name=settings.artifact_s3_region,
    )
    return S3ArtifactStore(
        client,
        settings.artifact_s3_bucket,
        kms_key_id=settings.artifact_s3_kms_key_id,
    )


def _policy_request(capability: Any, action: str) -> PolicyRequest:
    return PolicyRequest(
        subject=PolicySubject(
            id=capability.subject_id,
            tenantId=capability.tenant_id,
            roles=("workload",),
        ),
        action=action,
        resource={
            "projectId": capability.project_id,
            "artifactId": capability.artifact_id,
        },
        context={"runId": capability.run_id},
    )


def _blob_policy_request(capability: Any, action: str) -> PolicyRequest:
    return PolicyRequest(
        subject=PolicySubject(
            id=capability.subject_id,
            tenantId=capability.tenant_id,
            roles=("workload",),
        ),
        action=action,
        resource={
            "projectId": capability.project_id,
            "blobId": capability.blob_id,
        },
    )


def _set_trace_scope(request: Request, capability: Any) -> None:
    request.state.tenant_id = capability.tenant_id
    request.state.project_id = capability.project_id
    request.state.run_id = capability.run_id
    request.state.artifact_id = capability.artifact_id


def run() -> None:
    configure_json_logging()
    settings = Settings()
    telemetry = configure_telemetry(
        "artifact-gateway", endpoint=settings.otlp_endpoint, enabled=settings.telemetry_enabled
    )
    try:
        uvicorn.run(
            create_app(settings),
            host=settings.artifact_gateway_host,
            port=settings.artifact_gateway_port,
            **settings.workload_tls().uvicorn_options(),
        )
    finally:
        telemetry.shutdown()
