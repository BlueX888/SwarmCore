from __future__ import annotations

import contextlib
import hashlib
import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, Protocol

from .config import FilesystemToolConfig
from .errors import FilesystemErrorCode, FilesystemToolError
from .paths import (
    ResolvedPath,
    SafePathResolver,
    is_dir_nofollow,
    is_file_nofollow,
    is_link_or_reparse,
    path_lexists,
)


class FilesystemBackend(Protocol):
    async def healthy(self) -> bool: ...

    async def read_text(
        self,
        resolved: ResolvedPath,
        *,
        encoding: str,
        expected_sha256: str | None,
        max_bytes: int,
    ) -> dict[str, Any]: ...

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
    ) -> dict[str, Any]: ...

    async def list_dir(
        self,
        resolved: ResolvedPath,
        *,
        max_entries: int,
    ) -> dict[str, Any]: ...

    async def stat(self, resolved: ResolvedPath) -> dict[str, Any]: ...


@dataclass(frozen=True, slots=True)
class LocalFilesystemBackend:
    config: FilesystemToolConfig
    resolver: SafePathResolver

    async def healthy(self) -> bool:
        if not self.config.active:
            return False
        if self.config.mode.value != "local":
            return False
        if self.config.deployment_mode == "production":
            return False
        root = self.config.root.expanduser().resolve(strict=False)
        return root.exists() and root.is_dir()

    async def read_text(
        self,
        resolved: ResolvedPath,
        *,
        encoding: str,
        expected_sha256: str | None,
        max_bytes: int,
    ) -> dict[str, Any]:
        path = resolved.absolute_path
        _require_regular_file(path)
        size = path.stat().st_size
        if size > max_bytes:
            raise FilesystemToolError(
                FilesystemErrorCode.TOO_LARGE,
                "file exceeds the configured read limit",
            )
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise FilesystemToolError(
                FilesystemErrorCode.NOT_FOUND,
                "file was not found",
            ) from exc
        digest = hashlib.sha256(raw).hexdigest()
        if expected_sha256 is not None and expected_sha256 != digest:
            raise FilesystemToolError(
                FilesystemErrorCode.HASH_CONFLICT,
                "expectedSha256 does not match file content",
            )
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError as exc:
            raise FilesystemToolError(
                FilesystemErrorCode.ENCODING_ERROR,
                "file could not be decoded with the requested encoding",
            ) from exc
        if "\x00" in text:
            raise FilesystemToolError(
                FilesystemErrorCode.NOT_TEXT,
                "file contains binary content",
            )
        return {
            "mount": resolved.mount,
            "path": resolved.relative_path,
            "content": text,
            "encoding": encoding,
            "sizeBytes": len(raw),
            "sha256": digest,
        }

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
    ) -> dict[str, Any]:
        path = resolved.absolute_path
        try:
            raw = content.encode(encoding)
        except LookupError as exc:
            raise FilesystemToolError(
                FilesystemErrorCode.ENCODING_ERROR,
                "encoding is not supported",
            ) from exc
        except UnicodeEncodeError as exc:
            raise FilesystemToolError(
                FilesystemErrorCode.ENCODING_ERROR,
                "content could not be encoded",
            ) from exc
        if len(raw) > max_bytes:
            raise FilesystemToolError(
                FilesystemErrorCode.TOO_LARGE,
                "content exceeds the configured write limit",
            )
        exists = path_lexists(path)
        if exists and is_link_or_reparse(path):
            raise FilesystemToolError(
                FilesystemErrorCode.LINK_REJECTED,
                "symbolic links and reparse points are rejected",
            )
        if mode == "create" and exists:
            raise FilesystemToolError(
                FilesystemErrorCode.ALREADY_EXISTS,
                "file already exists",
            )
        if mode == "replace" and not exists:
            raise FilesystemToolError(
                FilesystemErrorCode.NOT_FOUND,
                "file was not found",
            )
        if exists:
            current = path.read_bytes()
            current_digest = hashlib.sha256(current).hexdigest()
            if expected_sha256 is None:
                raise FilesystemToolError(
                    FilesystemErrorCode.HASH_CONFLICT,
                    "expectedSha256 is required when replacing an existing file",
                )
            if expected_sha256 != current_digest:
                raise FilesystemToolError(
                    FilesystemErrorCode.HASH_CONFLICT,
                    "expectedSha256 does not match the current file",
                )
        elif expected_sha256 is not None:
            raise FilesystemToolError(
                FilesystemErrorCode.HASH_CONFLICT,
                "expectedSha256 was provided for a missing file",
            )

        parent = path.parent
        configured_root = self.config.root.expanduser().resolve(strict=False)
        if not configured_root.exists() or not configured_root.is_dir():
            raise FilesystemToolError(
                FilesystemErrorCode.NOT_FOUND,
                "filesystem root does not exist",
            )
        if not path_lexists(parent):
            _ensure_project_parent(parent, resolved.mount_root)
        if path_lexists(parent) and is_link_or_reparse(parent):
            raise FilesystemToolError(
                FilesystemErrorCode.LINK_REJECTED,
                "symbolic links and reparse points are rejected",
            )

        digest = hashlib.sha256(raw).hexdigest()
        staging = parent / f".swarmcore-write-{uuid.uuid4().hex}.tmp"
        created = not exists
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            nofollow = getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(staging, flags | nofollow, 0o600)
            try:
                with os.fdopen(fd, "wb") as handle:
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
            except Exception:
                with contextlib.suppress(OSError):
                    os.close(fd)
                raise
            os.replace(staging, path)
        except FilesystemToolError:
            _cleanup_temp(staging)
            raise
        except FileExistsError as exc:
            _cleanup_temp(staging)
            raise FilesystemToolError(
                FilesystemErrorCode.ALREADY_EXISTS,
                "file already exists",
            ) from exc
        except OSError as exc:
            _cleanup_temp(staging)
            raise FilesystemToolError(
                FilesystemErrorCode.PATH_INVALID,
                "write failed inside the project jail",
            ) from exc
        finally:
            _cleanup_temp(staging)

        return {
            "mount": resolved.mount,
            "path": resolved.relative_path,
            "created": created,
            "sizeBytes": len(raw),
            "sha256": digest,
            "effectId": effect_id,
        }

    async def list_dir(
        self,
        resolved: ResolvedPath,
        *,
        max_entries: int,
    ) -> dict[str, Any]:
        path = resolved.absolute_path
        if not path_lexists(path):
            raise FilesystemToolError(
                FilesystemErrorCode.NOT_FOUND,
                "directory was not found",
            )
        if is_link_or_reparse(path):
            raise FilesystemToolError(
                FilesystemErrorCode.LINK_REJECTED,
                "symbolic links and reparse points are rejected",
            )
        if not is_dir_nofollow(path):
            raise FilesystemToolError(
                FilesystemErrorCode.PATH_INVALID,
                "path is not a directory",
            )
        entries: list[dict[str, Any]] = []
        children = sorted(path.iterdir(), key=lambda item: item.name.casefold())
        if len(children) > max_entries:
            raise FilesystemToolError(
                FilesystemErrorCode.TOO_LARGE,
                "directory exceeds the configured list limit",
            )
        for child in children:
            if is_link_or_reparse(child):
                entry_type = "link"
                size = 0
                rejected_link = True
            elif is_dir_nofollow(child):
                entry_type = "directory"
                size = 0
                rejected_link = False
            elif is_file_nofollow(child):
                entry_type = "file"
                size = child.stat().st_size
                rejected_link = False
            else:
                entry_type = "other"
                size = 0
                rejected_link = False
            if resolved.relative_path in {".", ""}:
                relative = child.name
            else:
                relative = f"{resolved.relative_path}/{child.name}"
            entries.append(
                {
                    "name": child.name,
                    "path": relative,
                    "type": entry_type,
                    "sizeBytes": size,
                    "rejectedLink": rejected_link,
                }
            )
        return {
            "mount": resolved.mount,
            "path": resolved.relative_path,
            "entries": entries,
        }

    async def stat(self, resolved: ResolvedPath) -> dict[str, Any]:
        path = resolved.absolute_path
        if not path_lexists(path):
            raise FilesystemToolError(
                FilesystemErrorCode.NOT_FOUND,
                "path was not found",
            )
        rejected_link = is_link_or_reparse(path)
        if rejected_link:
            return {
                "mount": resolved.mount,
                "path": resolved.relative_path,
                "type": "link",
                "sizeBytes": 0,
                "modifiedAt": None,
                "sha256": None,
                "rejectedLink": True,
            }
        status = path.lstat()
        modified = (
            datetime.fromtimestamp(status.st_mtime, tz=UTC).isoformat().replace("+00:00", "Z")
        )
        if is_dir_nofollow(path):
            return {
                "mount": resolved.mount,
                "path": resolved.relative_path,
                "type": "directory",
                "sizeBytes": 0,
                "modifiedAt": modified,
                "sha256": None,
                "rejectedLink": False,
            }
        if not is_file_nofollow(path):
            return {
                "mount": resolved.mount,
                "path": resolved.relative_path,
                "type": "other",
                "sizeBytes": int(status.st_size),
                "modifiedAt": modified,
                "sha256": None,
                "rejectedLink": False,
            }
        raw = path.read_bytes()
        return {
            "mount": resolved.mount,
            "path": resolved.relative_path,
            "type": "file",
            "sizeBytes": len(raw),
            "modifiedAt": modified,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "rejectedLink": False,
        }


def _require_regular_file(path: Path) -> None:
    if not path_lexists(path):
        raise FilesystemToolError(
            FilesystemErrorCode.NOT_FOUND,
            "file was not found",
        )
    if is_link_or_reparse(path):
        raise FilesystemToolError(
            FilesystemErrorCode.LINK_REJECTED,
            "symbolic links and reparse points are rejected",
        )
    if not is_file_nofollow(path):
        raise FilesystemToolError(
            FilesystemErrorCode.PATH_INVALID,
            "path is not a regular file",
        )


def _ensure_project_parent(parent: Path, mount_root: Path) -> None:
    mount_resolved = mount_root.resolve(strict=False)
    try:
        parent.resolve(strict=False).relative_to(mount_resolved)
    except ValueError as exc:
        raise FilesystemToolError(
            FilesystemErrorCode.PATH_INVALID,
            "resolved path escapes the project jail",
        ) from exc
    parent.mkdir(parents=True, exist_ok=True)


def _cleanup_temp(path: Path) -> None:
    try:
        if path_lexists(path):
            path.unlink()
    except OSError:
        return
