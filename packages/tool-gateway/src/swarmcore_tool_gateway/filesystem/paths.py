from __future__ import annotations

import hashlib
import re
import stat as stat_module
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .errors import FilesystemErrorCode, FilesystemToolError

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_MOUNT_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_DRIVE_RE = re.compile(r"^[a-zA-Z]:([\\/]|$)")
_UNC_RE = re.compile(r"^(\\\\|//)")


def scope_segment(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or "\x00" in cleaned:
        raise FilesystemToolError(
            FilesystemErrorCode.PATH_INVALID,
            "tenant or project scope is invalid",
        )
    if _UUID_RE.fullmatch(cleaned):
        return cleaned.lower()
    digest = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:32]
    return f"id-{digest}"


@dataclass(frozen=True, slots=True)
class ResolvedPath:
    mount: str
    relative_path: str
    absolute_path: Path
    project_root: Path
    mount_root: Path


class SafePathResolver:
    """Resolve logical mount + relative path into a tenant/project jail."""

    def __init__(
        self,
        *,
        root: Path,
        allowed_mounts: frozenset[str],
        deny_names: frozenset[str],
    ) -> None:
        self._root = root.expanduser().resolve(strict=False)
        self._allowed_mounts = allowed_mounts
        self._deny_names = {name.casefold() for name in deny_names}

    def project_root(self, *, tenant_id: str, project_id: str) -> Path:
        return self._root / scope_segment(tenant_id) / scope_segment(project_id)

    def resolve(
        self,
        *,
        tenant_id: str,
        project_id: str,
        mount: str,
        relative_path: str,
    ) -> ResolvedPath:
        mount_name = self._require_mount(mount)
        relative = self._normalize_relative(relative_path)
        self._reject_sensitive(relative)
        project_root = self.project_root(tenant_id=tenant_id, project_id=project_id)
        mount_root = project_root / mount_name
        if relative.as_posix() == ".":
            candidate = mount_root.resolve(strict=False)
            logical = "."
        else:
            candidate = (mount_root / Path(*relative.parts)).resolve(strict=False)
            logical = relative.as_posix()
        self._assert_within(candidate, mount_root)
        self._assert_within(candidate, project_root)
        self._assert_within(candidate, self._root)
        self._reject_link_escape(candidate, mount_root)
        return ResolvedPath(
            mount=mount_name,
            relative_path=logical,
            absolute_path=candidate,
            project_root=project_root,
            mount_root=mount_root,
        )

    def _require_mount(self, mount: str) -> str:
        name = mount.strip()
        if not _MOUNT_RE.fullmatch(name):
            raise FilesystemToolError(
                FilesystemErrorCode.PATH_INVALID,
                "mount name is invalid",
            )
        if name not in self._allowed_mounts:
            raise FilesystemToolError(
                FilesystemErrorCode.MOUNT_UNAUTHORIZED,
                "mount is not authorized for this deployment",
            )
        return name

    def _normalize_relative(self, relative_path: str) -> PurePosixPath:
        raw = relative_path.strip()
        if not raw or "\x00" in raw:
            raise FilesystemToolError(
                FilesystemErrorCode.PATH_INVALID,
                "relative path is invalid",
            )
        if raw in {".", "./"}:
            return PurePosixPath(".")
        if _DRIVE_RE.match(raw) or _UNC_RE.match(raw):
            raise FilesystemToolError(
                FilesystemErrorCode.PATH_INVALID,
                "host absolute paths are not allowed",
            )
        if raw.startswith("/") or raw.startswith("\\"):
            raise FilesystemToolError(
                FilesystemErrorCode.PATH_INVALID,
                "absolute paths are not allowed",
            )
        normalized = PurePosixPath(raw.replace("\\", "/"))
        if normalized.is_absolute() or any(part in {"", ".", ".."} for part in normalized.parts):
            raise FilesystemToolError(
                FilesystemErrorCode.PATH_INVALID,
                "path escape sequences are not allowed",
            )
        return normalized

    def _reject_sensitive(self, relative: PurePosixPath) -> None:
        for part in relative.parts:
            folded = part.casefold()
            if folded in self._deny_names or folded.endswith(".pem") or folded.endswith(".key"):
                raise FilesystemToolError(
                    FilesystemErrorCode.PATH_DENIED,
                    "sensitive path is denied",
                )

    def _assert_within(self, candidate: Path, root: Path) -> None:
        root_resolved = root.resolve(strict=False)
        try:
            if not candidate.resolve(strict=False).is_relative_to(root_resolved):
                raise FilesystemToolError(
                    FilesystemErrorCode.PATH_INVALID,
                    "resolved path escapes the project jail",
                )
        except ValueError as exc:
            raise FilesystemToolError(
                FilesystemErrorCode.PATH_INVALID,
                "resolved path escapes the project jail",
            ) from exc

    def _reject_link_escape(self, candidate: Path, mount_root: Path) -> None:
        mount_resolved = mount_root.resolve(strict=False)
        try:
            relative_parts = candidate.resolve(strict=False).relative_to(mount_resolved).parts
        except ValueError as exc:
            raise FilesystemToolError(
                FilesystemErrorCode.PATH_INVALID,
                "resolved path escapes the project jail",
            ) from exc
        probe = mount_resolved
        for part in relative_parts:
            probe = probe / part
            if path_lexists(probe) and is_link_or_reparse(probe):
                raise FilesystemToolError(
                    FilesystemErrorCode.LINK_REJECTED,
                    "symbolic links and reparse points are rejected",
                )


def is_link_or_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        status = path.lstat()
    except OSError:
        return False
    attributes = getattr(status, "st_file_attributes", 0)
    reparse = getattr(stat_module, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse)


def path_lexists(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except OSError:
        return False
    return True


def is_dir_nofollow(path: Path) -> bool:
    try:
        status = path.lstat()
    except OSError:
        return False
    return stat_module.S_ISDIR(status.st_mode) and not is_link_or_reparse(path)


def is_file_nofollow(path: Path) -> bool:
    try:
        status = path.lstat()
    except OSError:
        return False
    return stat_module.S_ISREG(status.st_mode) and not is_link_or_reparse(path)
