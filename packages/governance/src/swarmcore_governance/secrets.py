from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator, Mapping
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class SecretError(RuntimeError):
    pass


_SECRET_REF = re.compile(r"^secret://[a-zA-Z0-9][a-zA-Z0-9_./-]{0,255}$")


def validate_secret_ref(secret_ref: str) -> str:
    if not _SECRET_REF.fullmatch(secret_ref) or ".." in secret_ref:
        raise SecretError("invalid secret reference")
    return secret_ref


@dataclass(frozen=True)
class SecretLease:
    values: Mapping[str, str]
    lease_id: str
    ttl_seconds: int


class SecretProvider(Protocol):
    def lease(self, secret_ref: str) -> AbstractAsyncContextManager[SecretLease]: ...


class InMemorySecretProvider:
    def __init__(self, secrets: Mapping[str, Mapping[str, str]]) -> None:
        self._secrets = secrets
        self.revoked: set[str] = set()
        self._sequence = 0

    @asynccontextmanager
    async def lease(self, secret_ref: str) -> AsyncIterator[SecretLease]:
        validate_secret_ref(secret_ref)
        if secret_ref not in self._secrets:
            raise SecretError("secret reference was not found")
        self._sequence += 1
        lease_id = f"memory/{self._sequence}"
        try:
            yield SecretLease(dict(self._secrets[secret_ref]), lease_id, 60)
        finally:
            self.revoked.add(lease_id)


class VaultSecretProvider:
    """Vault KV v2 and dynamic-secret adapter; only references cross the boundary."""

    def __init__(
        self,
        address: str,
        token: str = "",
        *,
        mount: str = "secret",
        kubernetes_role: str = "",
        kubernetes_jwt_path: str = (
            "/var/run/secrets/kubernetes.io/serviceaccount/token"
        ),
        kubernetes_auth_mount: str = "kubernetes",
    ) -> None:
        if not token and not kubernetes_role:
            raise SecretError("Vault authentication must be supplied by workload configuration")
        self._address = address.rstrip("/")
        self._token = token
        self._mount = mount
        self._kubernetes_role = kubernetes_role
        self._kubernetes_jwt_path = kubernetes_jwt_path
        self._kubernetes_auth_mount = kubernetes_auth_mount

    @asynccontextmanager
    async def lease(self, secret_ref: str) -> AsyncIterator[SecretLease]:
        path = validate_secret_ref(secret_ref).removeprefix("secret://")
        client_token, ephemeral_token = await self._client_token()
        try:
            dynamic = path.startswith("dynamic/")
            endpoint = (
                f"v1/{path.removeprefix('dynamic/')}"
                if dynamic
                else f"v1/{self._mount}/data/{path}"
            )
            raw = await asyncio.to_thread(self._request, endpoint, client_token)
            data = raw.get("data", {})
            values = data if dynamic else data.get("data") if isinstance(data, dict) else None
            if not isinstance(values, dict) or not all(
                isinstance(key, str) and isinstance(value, str) for key, value in values.items()
            ):
                raise SecretError("Vault secret does not contain string values")
            lease_id = str(raw.get("lease_id") or f"kv/{path}")
            duration = raw.get("lease_duration") or 60
            if not isinstance(duration, int) or duration < 1:
                raise SecretError("Vault returned an invalid lease duration")
            if dynamic and not raw.get("lease_id"):
                raise SecretError("Vault dynamic secret did not return a lease")
            lease = SecretLease(values, lease_id, duration)
            yield lease
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise SecretError(f"Vault read failed: {type(exc).__name__}") from exc
        finally:
            if "lease" in locals() and raw.get("lease_id"):
                await asyncio.to_thread(self._revoke, lease.lease_id, client_token)
            if ephemeral_token:
                await asyncio.to_thread(self._revoke_token, client_token)

    async def _client_token(self) -> tuple[str, bool]:
        if self._token:
            return self._token, False
        try:
            jwt = await asyncio.to_thread(
                Path(self._kubernetes_jwt_path).read_text, encoding="utf-8"
            )
            document = await asyncio.to_thread(self._login, jwt.strip())
            auth = document.get("auth")
            token = auth.get("client_token") if isinstance(auth, dict) else None
            if not isinstance(token, str) or not token:
                raise SecretError("Vault Kubernetes auth returned no client token")
            return token, True
        except (OSError, HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise SecretError(f"Vault Kubernetes auth failed: {type(exc).__name__}") from exc

    def _login(self, jwt: str) -> dict[str, Any]:
        payload = json.dumps({"role": self._kubernetes_role, "jwt": jwt}).encode()
        request = Request(
            f"{self._address}/v1/auth/{self._kubernetes_auth_mount}/login",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=3) as response:
            return cast(dict[str, Any], json.loads(response.read(1_048_576)))

    def _request(self, path: str, token: str | None = None) -> dict[str, Any]:
        request = Request(
            f"{self._address}/{path}",
            headers={"X-Vault-Token": token or self._token},
        )
        with urlopen(request, timeout=3) as response:
            return cast(dict[str, Any], json.loads(response.read(1_048_576)))

    def _revoke(self, lease_id: str, token: str | None = None) -> None:
        payload = json.dumps({"lease_id": lease_id}).encode()
        request = Request(
            f"{self._address}/v1/sys/leases/revoke",
            data=payload,
            headers={"X-Vault-Token": token or self._token, "Content-Type": "application/json"},
            method="PUT",
        )
        with urlopen(request, timeout=3):
            pass

    def _revoke_token(self, token: str) -> None:
        request = Request(
            f"{self._address}/v1/auth/token/revoke-self",
            data=b"{}",
            headers={"X-Vault-Token": token, "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=3):
            pass


class SecretScanner:
    def __init__(self, secrets: Mapping[str, str] | tuple[str, ...] | list[str]) -> None:
        values = secrets.values() if isinstance(secrets, Mapping) else secrets
        self._values = tuple(
            sorted((value for value in values if len(value) >= 4), key=len, reverse=True)
        )

    def redact(self, text: str) -> str:
        for value in self._values:
            text = text.replace(value, "[REDACTED]")
        return text

    def assert_clean(self, content: bytes) -> None:
        for value in self._values:
            if value.encode() in content:
                raise SecretError("content contains leased secret material")
