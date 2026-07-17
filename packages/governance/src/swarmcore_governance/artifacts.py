from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import mimetypes
import os
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from .audit import AuditRecord, AuditWriter
from .policy import PolicyEngine, PolicyRequest
from .secrets import SecretScanner


class ArtifactError(RuntimeError):
    pass


@dataclass(frozen=True)
class ArtifactCapability:
    action: str
    tenant_id: str
    project_id: str
    run_id: str
    subject_id: str
    artifact_id: str | None
    expires_at: int
    jti: str


class ArtifactCapabilityIssuer:
    def __init__(self, secret: bytes) -> None:
        if len(secret) < 32:
            raise ArtifactError("artifact capability secret must contain at least 32 bytes")
        self._secret = secret

    def issue(
        self,
        *,
        action: str,
        tenant_id: str,
        project_id: str,
        run_id: str,
        subject_id: str,
        artifact_id: str | None = None,
        ttl_seconds: int = 300,
    ) -> str:
        if action not in {"artifact.read", "artifact.write"}:
            raise ArtifactError("invalid artifact capability action")
        if action == "artifact.write" and artifact_id is None:
            raise ArtifactError("artifact.write capability must bind an artifact id")
        payload = {
            "action": action,
            "tenantId": tenant_id,
            "projectId": project_id,
            "runId": run_id,
            "subjectId": subject_id,
            "artifactId": artifact_id,
            "exp": int(time.time()) + min(ttl_seconds, 300),
            "jti": uuid4().hex,
        }
        encoded = _b64(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
        signature = _b64(hmac.digest(self._secret, encoded.encode(), "sha256"))
        return f"{encoded}.{signature}"

    def verify(self, token: str) -> ArtifactCapability:
        try:
            encoded, signature = token.split(".", 1)
            expected = _b64(hmac.digest(self._secret, encoded.encode(), "sha256"))
            if not hmac.compare_digest(signature, expected):
                raise ArtifactError("invalid artifact capability")
            payload = json.loads(_unb64(encoded))
            capability = ArtifactCapability(
                action=str(payload["action"]),
                tenant_id=str(payload["tenantId"]),
                project_id=str(payload["projectId"]),
                run_id=str(payload["runId"]),
                subject_id=str(payload["subjectId"]),
                artifact_id=(
                    str(payload["artifactId"]) if payload.get("artifactId") else None
                ),
                expires_at=int(payload["exp"]),
                jti=str(payload["jti"]),
            )
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ArtifactError("invalid artifact capability") from exc
        if capability.expires_at <= int(time.time()):
            raise ArtifactError("artifact capability expired")
        return capability


@dataclass(frozen=True)
class ArtifactRef:
    id: str
    tenant_id: str
    project_id: str
    run_id: str
    kind: str
    filename: str
    media_type: str
    size_bytes: int
    sha256: str
    status: str
    version: int = 1


class ArtifactStore(Protocol):
    async def put(self, object_key: str, content: bytes) -> None: ...
    async def get(self, object_key: str) -> bytes: ...
    async def delete(self, object_key: str) -> None: ...


class S3Client(Protocol):
    def put_object(self, **kwargs: object) -> object: ...
    def copy_object(self, **kwargs: object) -> object: ...
    def get_object(self, **kwargs: object) -> dict[str, object]: ...
    def delete_object(self, **kwargs: object) -> object: ...


class S3ArtifactStore:
    """S3 adapter using staging keys so partially uploaded bytes never become visible."""

    def __init__(self, client: S3Client, bucket: str, *, kms_key_id: str = "") -> None:
        self._client = client
        self._bucket = bucket
        self._kms_key_id = kms_key_id

    async def put(self, object_key: str, content: bytes) -> None:
        scope = object_key.split("/", 1)[0]
        if not scope or "/" not in object_key or object_key.startswith("/"):
            raise ArtifactError("S3 artifact key must begin with a tenant prefix")
        staging = f"{scope}/staging/{uuid4().hex}"
        encryption = self._encryption(scope)
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=staging,
            Body=content,
            **encryption,
        )
        try:
            await asyncio.to_thread(
                self._client.copy_object,
                Bucket=self._bucket,
                Key=object_key,
                CopySource={"Bucket": self._bucket, "Key": staging},
                MetadataDirective="COPY",
                **encryption,
            )
        finally:
            await asyncio.to_thread(
                self._client.delete_object, Bucket=self._bucket, Key=staging
            )

    async def get(self, object_key: str) -> bytes:
        response = await asyncio.to_thread(
            self._client.get_object, Bucket=self._bucket, Key=object_key
        )
        body = response.get("Body")
        if body is None or not hasattr(body, "read"):
            raise ArtifactError("S3 returned no artifact body")
        return await asyncio.to_thread(body.read)

    async def delete(self, object_key: str) -> None:
        await asyncio.to_thread(
            self._client.delete_object, Bucket=self._bucket, Key=object_key
        )

    def _encryption(self, tenant_id: str) -> dict[str, str]:
        if not self._kms_key_id:
            return {}
        return {
            "ServerSideEncryption": "aws:kms",
            "SSEKMSKeyId": self._kms_key_id,
            "SSEKMSEncryptionContext": json.dumps(
                {"tenantId": tenant_id}, sort_keys=True, separators=(",", ":")
            ),
        }


class ArtifactContentScanner(Protocol):
    async def scan(self, content: bytes) -> None: ...


class ClamAvScanner:
    def __init__(self, host: str, port: int = 3310, *, timeout_seconds: float = 10) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout_seconds

    async def scan(self, content: bytes) -> None:
        await asyncio.to_thread(self._scan, content)

    def _scan(self, content: bytes) -> None:
        import socket
        import struct

        with socket.create_connection((self._host, self._port), timeout=self._timeout) as stream:
            stream.sendall(b"zINSTREAM\0")
            for offset in range(0, len(content), 64 * 1024):
                chunk = content[offset : offset + 64 * 1024]
                stream.sendall(struct.pack(">I", len(chunk)) + chunk)
            stream.sendall(struct.pack(">I", 0))
            response = stream.recv(4096)
        if not response.endswith(b"OK\0"):
            raise ArtifactError("artifact malware scan rejected the content")


class LocalArtifactStore:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, object_key: str) -> Path:
        target = (self._root / object_key).resolve()
        if not target.is_relative_to(self._root):
            raise ArtifactError("artifact object key escapes the store root")
        return target

    async def put(self, object_key: str, content: bytes) -> None:
        target = self._path(object_key)
        staging = target.with_suffix(f".staging-{uuid4().hex}")
        target.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(staging.write_bytes, content)
        await asyncio.to_thread(os.replace, staging, target)

    async def get(self, object_key: str) -> bytes:
        try:
            return await asyncio.to_thread(self._path(object_key).read_bytes)
        except FileNotFoundError as exc:
            raise ArtifactError("artifact bytes were not found") from exc

    async def delete(self, object_key: str) -> None:
        try:
            await asyncio.to_thread(self._path(object_key).unlink)
        except FileNotFoundError:
            return


class ArtifactGateway:
    """Policy-enforced immutable artifact storage with one-time download grants."""

    def __init__(
        self,
        store: ArtifactStore,
        policy: PolicyEngine,
        audit: AuditWriter,
        signing_secret: bytes,
        *,
        max_artifact_bytes: int = 100 * 1024 * 1024,
        max_run_bytes: int = 1024 * 1024 * 1024,
        content_scanner: ArtifactContentScanner | None = None,
    ) -> None:
        if len(signing_secret) < 32:
            raise ArtifactError("artifact signing secret must contain at least 32 bytes")
        self._store = store
        self._policy = policy
        self._audit = audit
        self._secret = signing_secret
        self._max_artifact = max_artifact_bytes
        self._max_run = max_run_bytes
        self._content_scanner = content_scanner
        self._artifacts: dict[str, tuple[ArtifactRef, str]] = {}
        self._consumed_tokens: set[str] = set()
        self._lock = asyncio.Lock()

    async def upload(
        self,
        request: PolicyRequest,
        *,
        run_id: str,
        filename: str,
        media_type: str,
        kind: str,
        content: bytes,
        scanner: SecretScanner | None = None,
        artifact_id: str | None = None,
    ) -> ArtifactRef:
        decision = (await self._policy.evaluate(request)).enforce()
        limit = min(
            self._max_artifact,
            decision.obligations.max_bytes or self._max_artifact,
        )
        if not content or len(content) > limit:
            raise ArtifactError("artifact size is outside the allowed range")
        safe_name = Path(filename).name
        if safe_name != filename or safe_name in {"", ".", ".."}:
            raise ArtifactError("artifact filename is unsafe")
        expected_type = mimetypes.guess_type(safe_name)[0]
        if expected_type and media_type not in {expected_type, "application/octet-stream"}:
            raise ArtifactError("artifact MIME type does not match its filename")
        if scanner is not None:
            scanner.assert_clean(content)
        if self._content_scanner is not None:
            await self._content_scanner.scan(content)
        tenant_id = request.subject.tenant_id
        project_id = str(request.resource.get("projectId", ""))
        async with self._lock:
            used = sum(
                ref.size_bytes
                for ref, _ in self._artifacts.values()
                if ref.tenant_id == tenant_id and ref.run_id == run_id and ref.status == "AVAILABLE"
            )
            if used + len(content) > self._max_run:
                raise ArtifactError("run artifact quota would be exceeded")
            artifact_id = artifact_id or str(uuid4())
            object_key = f"{tenant_id}/{project_id}/{run_id}/{artifact_id}/v1"
            ref = ArtifactRef(
                id=artifact_id,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
                kind=kind,
                filename=safe_name,
                media_type=media_type,
                size_bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                status="SCANNING",
            )
            self._artifacts[artifact_id] = (ref, object_key)
        try:
            await self._store.put(object_key, content)
            ref = replace(ref, status="AVAILABLE")
            async with self._lock:
                self._artifacts[artifact_id] = (ref, object_key)
        except Exception:
            async with self._lock:
                self._artifacts[artifact_id] = (replace(ref, status="REJECTED"), object_key)
            raise
        await self._audit.append(
            AuditRecord(
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id=request.subject.id,
                action="artifact.upload",
                resource_type="artifact",
                resource_id=artifact_id,
                outcome="ALLOWED",
                policy_revision=decision.policy_revision,
                run_id=run_id,
                metadata={"sha256": ref.sha256, "sizeBytes": ref.size_bytes},
            )
        )
        return ref

    async def issue_download(
        self, request: PolicyRequest, artifact_id: str, *, ttl: int = 300
    ) -> str:
        decision = (await self._policy.evaluate(request)).enforce()
        ref = self._scoped_ref(request, artifact_id)
        if ref.status != "AVAILABLE":
            raise ArtifactError("artifact is not available")
        expires = int(time.time()) + min(ttl, 300)
        nonce = uuid4().hex
        payload = {
            "artifactId": artifact_id,
            "tenantId": ref.tenant_id,
            "exp": expires,
            "jti": nonce,
        }
        encoded = _b64(json.dumps(payload, separators=(",", ":")).encode())
        signature = _b64(hmac.digest(self._secret, encoded.encode(), "sha256"))
        await self._audit.append(
            AuditRecord(
                tenant_id=ref.tenant_id,
                project_id=ref.project_id,
                actor_id=request.subject.id,
                action="artifact.download.issue",
                resource_type="artifact",
                resource_id=ref.id,
                outcome="ALLOWED",
                policy_revision=decision.policy_revision,
                run_id=ref.run_id,
            )
        )
        return f"{encoded}.{signature}"

    async def download(self, token: str) -> tuple[ArtifactRef, bytes]:
        try:
            encoded, signature = token.split(".", 1)
            expected = _b64(hmac.digest(self._secret, encoded.encode(), "sha256"))
            if not hmac.compare_digest(signature, expected):
                raise ArtifactError("invalid artifact download grant")
            payload = json.loads(_unb64(encoded))
            if int(payload["exp"]) < int(time.time()):
                raise ArtifactError("artifact download grant expired")
            jti = str(payload["jti"])
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ArtifactError("invalid artifact download grant") from exc
        async with self._lock:
            if jti in self._consumed_tokens:
                raise ArtifactError("artifact download grant was already consumed")
            self._consumed_tokens.add(jti)
            ref, object_key = self._artifacts[str(payload["artifactId"])]
        if ref.tenant_id != payload["tenantId"] or ref.status != "AVAILABLE":
            raise ArtifactError("artifact download grant is outside its scope")
        content = await self._store.get(object_key)
        if hashlib.sha256(content).hexdigest() != ref.sha256:
            raise ArtifactError("artifact integrity check failed")
        return ref, content

    def list(self, request: PolicyRequest, *, run_id: str | None = None) -> tuple[ArtifactRef, ...]:
        refs = (
            ref
            for ref, _ in self._artifacts.values()
            if ref.tenant_id == request.subject.tenant_id
            and ref.project_id == request.resource.get("projectId")
        )
        if run_id is not None:
            refs = (ref for ref in refs if ref.run_id == run_id)
        return tuple(refs)

    def _scoped_ref(self, request: PolicyRequest, artifact_id: str) -> ArtifactRef:
        try:
            ref, _ = self._artifacts[artifact_id]
        except KeyError as exc:
            raise ArtifactError("artifact was not found") from exc
        if (
            ref.tenant_id != request.subject.tenant_id
            or ref.project_id != request.resource.get("projectId")
        ):
            raise ArtifactError("artifact was not found")
        return ref


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
