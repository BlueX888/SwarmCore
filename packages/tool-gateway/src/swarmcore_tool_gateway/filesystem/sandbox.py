from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Literal, Protocol

from swarmcore_governance import (
    PolicyDecision,
    PolicyObligations,
    SandboxAdmission,
    SandboxCapabilityIssuer,
    SandboxRequest,
    SandboxViolation,
)

from .config import FilesystemToolConfig
from .errors import FilesystemErrorCode, FilesystemToolError
from .paths import ResolvedPath


@dataclass(frozen=True, slots=True)
class FilesystemSandboxTask:
    """Declared sandbox I/O contract for filesystem tools.

    Content may travel only through the task payload for the helper process.
    Host absolute paths are never included.
    """

    operation: Literal["read_text", "write_text", "list", "stat"]
    mount: str
    relative_path: str
    tenant_scope: str
    project_scope: str
    run_id: str
    effect_id: str
    encoding: str | None = None
    content: str | None = None
    mode: Literal["create", "replace"] | None = None
    expected_sha256: str | None = None
    max_bytes: int | None = None
    max_entries: int | None = None


class SandboxFilesystemTransport(Protocol):
    async def available(self) -> bool: ...

    async def execute(self, task: FilesystemSandboxTask) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class HttpSandboxFilesystemTransport:
    """Submit a digest-pinned filesystem helper Job through Sandbox Manager."""

    config: FilesystemToolConfig

    async def available(self) -> bool:
        if not self.config.sandbox_base_url.strip():
            return False
        if not self.config.sandbox_image.strip() or "@sha256:" not in self.config.sandbox_image:
            return False
        return len(self.config.sandbox_capability_secret.encode()) >= 32

    async def execute(self, task: FilesystemSandboxTask) -> dict[str, Any]:
        if not await self.available():
            raise FilesystemToolError(
                FilesystemErrorCode.SANDBOX_UNAVAILABLE,
                "sandbox filesystem transport is not configured",
            )
        try:
            job = self._admit(task)
        except SandboxViolation as exc:
            raise FilesystemToolError(
                FilesystemErrorCode.SANDBOX_UNAVAILABLE,
                "sandbox admission rejected the filesystem task",
            ) from exc
        issuer = SandboxCapabilityIssuer(self.config.sandbox_capability_secret.encode())
        token = issuer.issue(
            tenant_id=task.tenant_scope,
            project_id=task.project_scope,
            run_id=task.run_id,
            task_execution_id=task.effect_id,
            subject_id=f"filesystem:{task.operation}",
            ttl_seconds=min(300, self.config.sandbox_timeout_seconds + 30),
        )
        body = {
            "capabilityToken": token,
            "image": job.request.image,
            "command": list(job.request.command),
            "cpuMillis": job.request.cpu_millis,
            "memoryMib": job.request.memory_mib,
            "workspaceMib": job.request.workspace_mib,
            "timeoutSeconds": job.request.timeout_seconds,
            "networkTargets": list(job.request.network_targets),
            "privileged": False,
            "hostPaths": [],
            "filesystemTask": {
                "operation": task.operation,
                "mount": task.mount,
                "path": task.relative_path,
                "encoding": task.encoding,
                "mode": task.mode,
                "expectedSha256": task.expected_sha256,
                "maxBytes": task.max_bytes,
                "maxEntries": task.max_entries,
                # Content is exchanged only through the declared task contract.
                "content": task.content,
            },
        }
        try:
            response = await _post_json(
                f"{self.config.sandbox_base_url.rstrip('/')}/internal/v1/sandboxes",
                body,
            )
        except FilesystemToolError:
            raise
        except Exception as exc:
            raise FilesystemToolError(
                FilesystemErrorCode.SANDBOX_UNAVAILABLE,
                "sandbox manager is unavailable",
            ) from exc
        status = str(response.get("status") or "")
        result = response.get("result")
        if status != "SUCCEEDED" or not isinstance(result, dict):
            # Fail closed: SUBMITTED/dry-run without a declared result is not success.
            raise FilesystemToolError(
                FilesystemErrorCode.SANDBOX_UNAVAILABLE,
                "sandbox filesystem execution did not return a declared result",
            )
        return result

    def _admit(self, task: FilesystemSandboxTask) -> Any:
        admission = SandboxAdmission(allowed_images=frozenset({self.config.sandbox_image}))
        request = SandboxRequest(
            image=self.config.sandbox_image,
            command=(
                "swarmcore-filesystem-helper",
                "--operation",
                task.operation,
                "--mount",
                task.mount,
                "--path",
                task.relative_path,
            ),
            cpu_millis=self.config.sandbox_cpu_millis,
            memory_mib=self.config.sandbox_memory_mib,
            workspace_mib=self.config.sandbox_workspace_mib,
            timeout_seconds=self.config.sandbox_timeout_seconds,
            network_targets=(),
            privileged=False,
            host_paths=(),
        )
        decision = PolicyDecision(
            allow=True,
            obligations=PolicyObligations(
                maxDurationSeconds=max(self.config.sandbox_timeout_seconds, 1),
                allowedEgress=(),
            ),
            policyRevision="filesystem-sandbox",
        )
        return admission.admit(request, decision)


@dataclass(frozen=True, slots=True)
class SandboxFilesystemBackend:
    config: FilesystemToolConfig
    transport: SandboxFilesystemTransport

    async def healthy(self) -> bool:
        if not self.config.active:
            return False
        if self.config.mode.value != "sandbox":
            return False
        return await self.transport.available()

    async def read_text(
        self,
        resolved: ResolvedPath,
        *,
        encoding: str,
        expected_sha256: str | None,
        max_bytes: int,
        tenant_id: str,
        project_id: str,
        run_id: str,
        effect_id: str,
    ) -> dict[str, Any]:
        return await self.transport.execute(
            FilesystemSandboxTask(
                operation="read_text",
                mount=resolved.mount,
                relative_path=resolved.relative_path,
                tenant_scope=tenant_id,
                project_scope=project_id,
                run_id=run_id,
                effect_id=effect_id,
                encoding=encoding,
                expected_sha256=expected_sha256,
                max_bytes=max_bytes,
            )
        )

    async def write_text(
        self,
        resolved: ResolvedPath,
        *,
        content: str,
        encoding: str,
        mode: Literal["create", "replace"],
        expected_sha256: str | None,
        effect_id: str,
        max_bytes: int,
        tenant_id: str,
        project_id: str,
        run_id: str,
    ) -> dict[str, Any]:
        return await self.transport.execute(
            FilesystemSandboxTask(
                operation="write_text",
                mount=resolved.mount,
                relative_path=resolved.relative_path,
                tenant_scope=tenant_id,
                project_scope=project_id,
                run_id=run_id,
                effect_id=effect_id,
                encoding=encoding,
                content=content,
                mode=mode,
                expected_sha256=expected_sha256,
                max_bytes=max_bytes,
            )
        )

    async def list_dir(
        self,
        resolved: ResolvedPath,
        *,
        max_entries: int,
        tenant_id: str,
        project_id: str,
        run_id: str,
        effect_id: str,
    ) -> dict[str, Any]:
        return await self.transport.execute(
            FilesystemSandboxTask(
                operation="list",
                mount=resolved.mount,
                relative_path=resolved.relative_path,
                tenant_scope=tenant_id,
                project_scope=project_id,
                run_id=run_id,
                effect_id=effect_id,
                max_entries=max_entries,
            )
        )

    async def stat(
        self,
        resolved: ResolvedPath,
        *,
        tenant_id: str,
        project_id: str,
        run_id: str,
        effect_id: str,
    ) -> dict[str, Any]:
        return await self.transport.execute(
            FilesystemSandboxTask(
                operation="stat",
                mount=resolved.mount,
                relative_path=resolved.relative_path,
                tenant_scope=tenant_id,
                project_scope=project_id,
                run_id=run_id,
                effect_id=effect_id,
            )
        )


async def _post_json(url: str, body: dict[str, Any]) -> dict[str, Any]:
    payload = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    def _call() -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise FilesystemToolError(
                FilesystemErrorCode.SANDBOX_UNAVAILABLE,
                f"sandbox manager returned HTTP {exc.code}",
            ) from exc
        except urllib.error.URLError as exc:
            raise FilesystemToolError(
                FilesystemErrorCode.SANDBOX_UNAVAILABLE,
                "sandbox manager is unreachable",
            ) from exc
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FilesystemToolError(
                FilesystemErrorCode.SANDBOX_UNAVAILABLE,
                "sandbox manager returned an invalid payload",
            ) from exc
        if not isinstance(parsed, dict):
            raise FilesystemToolError(
                FilesystemErrorCode.SANDBOX_UNAVAILABLE,
                "sandbox manager returned an invalid payload",
            )
        return parsed

    import asyncio

    return await asyncio.to_thread(_call)
