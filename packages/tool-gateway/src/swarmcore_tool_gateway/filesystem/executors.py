from __future__ import annotations

from typing import Any, Literal

from ..gateway import ToolExecutionContext
from .config import FilesystemExecutorMode, FilesystemToolConfig
from .errors import FilesystemErrorCode, FilesystemToolError
from .local import LocalFilesystemBackend
from .paths import SafePathResolver
from .sandbox import (
    HttpSandboxFilesystemTransport,
    SandboxFilesystemBackend,
    SandboxFilesystemTransport,
)


class FilesystemToolService:
    def __init__(
        self,
        config: FilesystemToolConfig,
        *,
        sandbox_transport: SandboxFilesystemTransport | None = None,
    ) -> None:
        config.validate()
        self._config = config
        self._resolver = SafePathResolver(
            root=config.root,
            allowed_mounts=config.allowed_mounts,
            deny_names=config.deny_names,
        )
        self._local = LocalFilesystemBackend(config=config, resolver=self._resolver)
        transport = sandbox_transport or HttpSandboxFilesystemTransport(config)
        self._sandbox = SandboxFilesystemBackend(config=config, transport=transport)

    @property
    def config(self) -> FilesystemToolConfig:
        return self._config

    @property
    def resolver(self) -> SafePathResolver:
        return self._resolver

    async def healthy(self) -> bool:
        if not self._config.active:
            return False
        if self._config.mode is FilesystemExecutorMode.LOCAL:
            return await self._local.healthy()
        if self._config.mode is FilesystemExecutorMode.SANDBOX:
            return await self._sandbox.healthy()
        return False

    def _ensure_enabled(self) -> None:
        if not self._config.active:
            raise FilesystemToolError(
                FilesystemErrorCode.TOOL_DISABLED,
                "filesystem tools are disabled",
            )
        if (
            self._config.deployment_mode == "production"
            and self._config.mode is FilesystemExecutorMode.LOCAL
        ):
            raise FilesystemToolError(
                FilesystemErrorCode.MODE_FORBIDDEN,
                "local filesystem mode is forbidden in production",
            )

    async def read_text(
        self,
        input_value: dict[str, Any],
        effect_id: str,
        context: ToolExecutionContext,
    ) -> dict[str, Any]:
        del effect_id
        self._ensure_enabled()
        resolved = self._resolver.resolve(
            tenant_id=context.tenant_id,
            project_id=context.project_id,
            mount=str(input_value["mount"]),
            relative_path=str(input_value["path"]),
        )
        encoding = str(input_value.get("encoding") or "utf-8")
        expected = input_value.get("expectedSha256")
        expected_sha = str(expected) if expected is not None else None
        if self._config.mode is FilesystemExecutorMode.SANDBOX:
            return await self._sandbox.read_text(
                resolved,
                encoding=encoding,
                expected_sha256=expected_sha,
                max_bytes=self._config.max_read_bytes,
                tenant_id=context.tenant_id,
                project_id=context.project_id,
                run_id=context.run_id,
                effect_id=context.execution_id,
            )
        return await self._local.read_text(
            resolved,
            encoding=encoding,
            expected_sha256=expected_sha,
            max_bytes=self._config.max_read_bytes,
        )

    async def write_text(
        self,
        input_value: dict[str, Any],
        effect_id: str,
        context: ToolExecutionContext,
    ) -> dict[str, Any]:
        self._ensure_enabled()
        resolved = self._resolver.resolve(
            tenant_id=context.tenant_id,
            project_id=context.project_id,
            mount=str(input_value["mount"]),
            relative_path=str(input_value["path"]),
        )
        encoding = str(input_value.get("encoding") or "utf-8")
        mode = str(input_value.get("mode") or "create")
        if mode not in {"create", "replace"}:
            raise FilesystemToolError(
                FilesystemErrorCode.PATH_INVALID,
                "write mode must be create or replace",
            )
        write_mode: Literal["create", "replace"] = "create" if mode == "create" else "replace"
        expected = input_value.get("expectedSha256")
        expected_sha = str(expected) if expected is not None else None
        if self._config.mode is FilesystemExecutorMode.SANDBOX:
            return await self._sandbox.write_text(
                resolved,
                content=str(input_value["content"]),
                encoding=encoding,
                mode=write_mode,
                expected_sha256=expected_sha,
                effect_id=effect_id,
                max_bytes=self._config.max_write_bytes,
                tenant_id=context.tenant_id,
                project_id=context.project_id,
                run_id=context.run_id,
            )
        return await self._local.write_text(
            resolved,
            content=str(input_value["content"]),
            encoding=encoding,
            mode=write_mode,
            expected_sha256=expected_sha,
            effect_id=effect_id,
            max_bytes=self._config.max_write_bytes,
        )

    async def list_entries(
        self,
        input_value: dict[str, Any],
        effect_id: str,
        context: ToolExecutionContext,
    ) -> dict[str, Any]:
        del effect_id
        self._ensure_enabled()
        resolved = self._resolver.resolve(
            tenant_id=context.tenant_id,
            project_id=context.project_id,
            mount=str(input_value["mount"]),
            relative_path=str(input_value["path"]),
        )
        if self._config.mode is FilesystemExecutorMode.SANDBOX:
            return await self._sandbox.list_dir(
                resolved,
                max_entries=self._config.max_list_entries,
                tenant_id=context.tenant_id,
                project_id=context.project_id,
                run_id=context.run_id,
                effect_id=context.execution_id,
            )
        return await self._local.list_dir(
            resolved,
            max_entries=self._config.max_list_entries,
        )

    async def stat_path(
        self,
        input_value: dict[str, Any],
        effect_id: str,
        context: ToolExecutionContext,
    ) -> dict[str, Any]:
        del effect_id
        self._ensure_enabled()
        resolved = self._resolver.resolve(
            tenant_id=context.tenant_id,
            project_id=context.project_id,
            mount=str(input_value["mount"]),
            relative_path=str(input_value["path"]),
        )
        if self._config.mode is FilesystemExecutorMode.SANDBOX:
            return await self._sandbox.stat(
                resolved,
                tenant_id=context.tenant_id,
                project_id=context.project_id,
                run_id=context.run_id,
                effect_id=context.execution_id,
            )
        return await self._local.stat(resolved)


class _FilesystemExecutor:
    operation: str

    def __init__(self, service: FilesystemToolService) -> None:
        self._service = service

    async def healthy(self) -> bool:
        return await self._service.healthy()


class ReadTextExecutor(_FilesystemExecutor):
    operation = "filesystem.read_text"

    async def execute(
        self,
        input_value: dict[str, Any],
        effect_id: str,
        context: ToolExecutionContext,
    ) -> dict[str, Any]:
        return await self._service.read_text(input_value, effect_id, context)


class WriteTextExecutor(_FilesystemExecutor):
    operation = "filesystem.write_text"

    async def execute(
        self,
        input_value: dict[str, Any],
        effect_id: str,
        context: ToolExecutionContext,
    ) -> dict[str, Any]:
        return await self._service.write_text(input_value, effect_id, context)


class ListExecutor(_FilesystemExecutor):
    operation = "filesystem.list"

    async def execute(
        self,
        input_value: dict[str, Any],
        effect_id: str,
        context: ToolExecutionContext,
    ) -> dict[str, Any]:
        return await self._service.list_entries(input_value, effect_id, context)


class StatExecutor(_FilesystemExecutor):
    operation = "filesystem.stat"

    async def execute(
        self,
        input_value: dict[str, Any],
        effect_id: str,
        context: ToolExecutionContext,
    ) -> dict[str, Any]:
        return await self._service.stat_path(input_value, effect_id, context)
