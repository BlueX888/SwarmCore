from __future__ import annotations

import base64
import hashlib
import hmac
import ipaddress
import json
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from .policy import PolicyDecision


class SandboxViolation(RuntimeError):
    pass


@dataclass(frozen=True)
class SandboxCapability:
    tenant_id: str
    project_id: str
    run_id: str
    task_execution_id: str
    subject_id: str
    expires_at: int
    jti: str


class SandboxCapabilityIssuer:
    def __init__(self, secret: bytes) -> None:
        if len(secret) < 32:
            raise SandboxViolation("sandbox capability secret must contain at least 32 bytes")
        self._secret = secret

    def issue(
        self,
        *,
        tenant_id: str,
        project_id: str,
        run_id: str,
        task_execution_id: str,
        subject_id: str,
        ttl_seconds: int = 300,
    ) -> str:
        payload = {
            "tenantId": tenant_id,
            "projectId": project_id,
            "runId": run_id,
            "taskExecutionId": task_execution_id,
            "subjectId": subject_id,
            "exp": int(time.time()) + min(ttl_seconds, 300),
            "jti": uuid4().hex,
        }
        encoded = _encode(payload)
        signature = _b64(hmac.new(self._secret, encoded.encode(), hashlib.sha256).digest())
        return f"{encoded}.{signature}"

    def verify(self, token: str) -> SandboxCapability:
        try:
            encoded, signature = token.split(".", 1)
            expected = _b64(hmac.new(self._secret, encoded.encode(), hashlib.sha256).digest())
            if not hmac.compare_digest(signature, expected):
                raise SandboxViolation("invalid sandbox capability")
            payload: dict[str, Any] = json.loads(_decode(encoded))
            capability = SandboxCapability(
                tenant_id=str(payload["tenantId"]),
                project_id=str(payload["projectId"]),
                run_id=str(payload["runId"]),
                task_execution_id=str(payload["taskExecutionId"]),
                subject_id=str(payload["subjectId"]),
                expires_at=int(payload["exp"]),
                jti=str(payload["jti"]),
            )
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise SandboxViolation("invalid sandbox capability") from exc
        if capability.expires_at <= int(time.time()):
            raise SandboxViolation("sandbox capability expired")
        return capability


@dataclass(frozen=True)
class SandboxRequest:
    image: str
    command: tuple[str, ...]
    cpu_millis: int
    memory_mib: int
    workspace_mib: int
    timeout_seconds: int
    network_targets: tuple[str, ...] = ()
    privileged: bool = False
    host_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class SandboxJob:
    runtime_class: str
    read_only_root_filesystem: bool
    run_as_non_root: bool
    seccomp_profile: str
    automount_service_account_token: bool
    request: SandboxRequest


class SandboxAdmission:
    def __init__(
        self,
        *,
        allowed_images: frozenset[str],
        max_cpu_millis: int = 2000,
        max_memory_mib: int = 2048,
        max_workspace_mib: int = 1024,
    ) -> None:
        self._images = allowed_images
        self._max_cpu = max_cpu_millis
        self._max_memory = max_memory_mib
        self._max_workspace = max_workspace_mib

    def admit(self, request: SandboxRequest, decision: PolicyDecision) -> SandboxJob:
        decision.enforce()
        if request.image not in self._images or "@sha256:" not in request.image:
            raise SandboxViolation("sandbox image must be allowlisted and digest pinned")
        if request.privileged or request.host_paths:
            raise SandboxViolation("privileged mode and host path mounts are forbidden")
        if not request.command:
            raise SandboxViolation("sandbox command is required")
        if not 1 <= request.cpu_millis <= self._max_cpu:
            raise SandboxViolation("sandbox CPU limit is invalid")
        if not 1 <= request.memory_mib <= self._max_memory:
            raise SandboxViolation("sandbox memory limit is invalid")
        if not 1 <= request.workspace_mib <= self._max_workspace:
            raise SandboxViolation("sandbox workspace limit is invalid")
        policy_timeout = decision.obligations.max_duration_seconds or 300
        if not 1 <= request.timeout_seconds <= policy_timeout:
            raise SandboxViolation("sandbox timeout exceeds the policy obligation")
        allowed = set(decision.obligations.allowed_egress)
        for target in request.network_targets:
            if target not in allowed:
                raise SandboxViolation("sandbox network target is not allowed")
            try:
                host, raw_port = target.rsplit(":", 1)
                port = int(raw_port)
            except (TypeError, ValueError) as exc:
                raise SandboxViolation(
                    "sandbox network target must be a global IP and port"
                ) from exc
            host = host.removeprefix("[").removesuffix("]")
            if not 1 <= port <= 65535:
                raise SandboxViolation("sandbox network target port is invalid")
            try:
                ip = ipaddress.ip_address(host)
            except ValueError as exc:
                raise SandboxViolation(
                    "sandbox network target must use a pinned IP address"
                ) from exc
            if not ip.is_global:
                raise SandboxViolation("sandbox cannot access private or metadata addresses")
        return SandboxJob(
            runtime_class="gvisor",
            read_only_root_filesystem=True,
            run_as_non_root=True,
            seccomp_profile="RuntimeDefault",
            automount_service_account_token=False,
            request=request,
        )


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _encode(value: dict[str, Any]) -> str:
    return _b64(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
