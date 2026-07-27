from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..builtins import builtin_executors
from .config import FilesystemToolConfig
from .executors import (
    FilesystemToolService,
    ListExecutor,
    ReadTextExecutor,
    StatExecutor,
    WriteTextExecutor,
)
from .sandbox import SandboxFilesystemTransport


def filesystem_executors(
    config: FilesystemToolConfig | None = None,
    *,
    sandbox_transport: SandboxFilesystemTransport | None = None,
) -> dict[str, Any]:
    """Shared factory used by Tool Gateway API and worker-tool."""

    service = FilesystemToolService(
        config or FilesystemToolConfig(),
        sandbox_transport=sandbox_transport,
    )
    return {
        ReadTextExecutor.operation: ReadTextExecutor(service),
        WriteTextExecutor.operation: WriteTextExecutor(service),
        ListExecutor.operation: ListExecutor(service),
        StatExecutor.operation: StatExecutor(service),
    }


def assemble_tool_executors(
    *,
    filesystem: FilesystemToolConfig | None = None,
    extra: Mapping[str, Any] | None = None,
    sandbox_transport: SandboxFilesystemTransport | None = None,
) -> dict[str, Any]:
    """Compose builtin, filesystem, and capability executors without duplication."""

    return {
        **builtin_executors(),
        **filesystem_executors(filesystem, sandbox_transport=sandbox_transport),
        **dict(extra or {}),
    }
