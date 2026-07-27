from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Literal


class FilesystemExecutorMode(StrEnum):
    DISABLED = "disabled"
    LOCAL = "local"
    SANDBOX = "sandbox"


DEFAULT_DENY_NAMES: frozenset[str] = frozenset(
    {
        ".env",
        ".env.local",
        ".env.production",
        ".git",
        ".gitignore",
        ".ssh",
        ".aws",
        ".azure",
        ".config",
        ".kube",
        ".gnupg",
        ".docker",
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        "authorized_keys",
        "known_hosts",
        "credentials",
        "credentials.json",
        "service-account.json",
        "vault-token",
        "token",
        "secret",
        "secrets",
        ".vault-token",
        "terraform.tfstate",
    }
)


@dataclass(frozen=True, slots=True)
class FilesystemToolConfig:
    enabled: bool = False
    root: Path = Path(".tmp/filesystem")
    allowed_mounts: frozenset[str] = frozenset({"workspace"})
    max_read_bytes: int = 1_048_576
    max_write_bytes: int = 1_048_576
    max_list_entries: int = 1_000
    deny_names: frozenset[str] = field(default_factory=lambda: DEFAULT_DENY_NAMES)
    mode: FilesystemExecutorMode = FilesystemExecutorMode.DISABLED
    deployment_mode: Literal["local", "production"] = "local"
    sandbox_base_url: str = ""
    sandbox_image: str = ""
    sandbox_capability_secret: str = ""
    sandbox_timeout_seconds: int = 60
    sandbox_cpu_millis: int = 500
    sandbox_memory_mib: int = 256
    sandbox_workspace_mib: int = 256

    def validate(self) -> None:
        if self.deployment_mode == "production" and self.mode is FilesystemExecutorMode.LOCAL:
            raise ValueError("production filesystem tools forbid local executor mode")
        if self.mode is FilesystemExecutorMode.SANDBOX:
            if not self.sandbox_base_url.strip():
                raise ValueError("sandbox filesystem mode requires sandbox_base_url")
            if not self.sandbox_image.strip() or "@sha256:" not in self.sandbox_image:
                raise ValueError("sandbox filesystem mode requires a digest-pinned image")
            if len(self.sandbox_capability_secret.encode()) < 32:
                raise ValueError("sandbox filesystem mode requires a capability secret")
        if self.max_read_bytes < 1 or self.max_write_bytes < 1 or self.max_list_entries < 1:
            raise ValueError("filesystem size and list limits must be positive")
        for mount in self.allowed_mounts:
            if not mount or "/" in mount or "\\" in mount or mount in {".", ".."}:
                raise ValueError(f"invalid filesystem mount name: {mount!r}")

    @property
    def active(self) -> bool:
        return self.enabled and self.mode is not FilesystemExecutorMode.DISABLED
