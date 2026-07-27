from __future__ import annotations

from enum import StrEnum


class FilesystemErrorCode(StrEnum):
    TOOL_DISABLED = "FILESYSTEM_TOOL_DISABLED"
    MOUNT_UNAUTHORIZED = "FILESYSTEM_MOUNT_UNAUTHORIZED"
    PATH_INVALID = "FILESYSTEM_PATH_INVALID"
    PATH_DENIED = "FILESYSTEM_PATH_DENIED"
    NOT_FOUND = "FILESYSTEM_NOT_FOUND"
    ALREADY_EXISTS = "FILESYSTEM_ALREADY_EXISTS"
    HASH_CONFLICT = "FILESYSTEM_HASH_CONFLICT"
    TOO_LARGE = "FILESYSTEM_TOO_LARGE"
    NOT_TEXT = "FILESYSTEM_NOT_TEXT"
    ENCODING_ERROR = "FILESYSTEM_ENCODING_ERROR"
    LINK_REJECTED = "FILESYSTEM_LINK_REJECTED"
    SANDBOX_UNAVAILABLE = "FILESYSTEM_SANDBOX_UNAVAILABLE"
    MODE_FORBIDDEN = "FILESYSTEM_MODE_FORBIDDEN"


class FilesystemToolError(ValueError):
    """Stable, auditable filesystem tool failure without host paths or content."""

    def __init__(self, code: FilesystemErrorCode, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")
