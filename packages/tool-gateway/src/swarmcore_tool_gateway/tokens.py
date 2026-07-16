from __future__ import annotations

import base64
import hashlib
import hmac
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class TokenError(ValueError):
    pass


class CapabilityClaims(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    issuer: str = Field(alias="iss")
    audience: str = Field(alias="aud")
    tenant_id: str = Field(alias="tenantId")
    project_id: str = Field(alias="projectId")
    run_id: str = Field(alias="runId")
    node_key: str = Field(alias="nodeKey")
    tool_ref: str = Field(alias="toolRef")
    execution_id: str = Field(alias="executionId")
    effect_id: str | None = Field(default=None, alias="effectId")
    approved: bool = False
    issued_at: int = Field(alias="iat")
    expires_at: int = Field(alias="exp")


class CapabilityTokenIssuer:
    def __init__(
        self,
        secret: str,
        *,
        issuer: str = "swarmcore-control",
        audience: str = "swarmcore-tool-gateway",
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if len(secret.encode()) < 32:
            raise ValueError("capability token secret must contain at least 32 bytes")
        self._secret = secret.encode()
        self._issuer = issuer
        self._audience = audience
        self._clock = clock or (lambda: datetime.now(UTC))

    def issue(
        self,
        *,
        tenant_id: str,
        project_id: str,
        run_id: str,
        node_key: str,
        tool_ref: str,
        execution_id: str,
        effect_id: str | None,
        approved: bool,
        ttl: timedelta = timedelta(minutes=15),
    ) -> str:
        now = self._clock()
        claims = CapabilityClaims(
            iss=self._issuer,
            aud=self._audience,
            tenantId=tenant_id,
            projectId=project_id,
            runId=run_id,
            nodeKey=node_key,
            toolRef=tool_ref,
            executionId=execution_id,
            effectId=effect_id,
            approved=approved,
            iat=int(now.timestamp()),
            exp=int((now + ttl).timestamp()),
        )
        header = _encode({"alg": "HS256", "typ": "SCCT"})
        payload = _encode(claims.model_dump(mode="json", by_alias=True))
        unsigned = f"{header}.{payload}"
        signature = _b64(hmac.new(self._secret, unsigned.encode(), hashlib.sha256).digest())
        return f"{unsigned}.{signature}"

    def verify(self, token: str) -> CapabilityClaims:
        parts = token.split(".")
        if len(parts) != 3:
            raise TokenError("malformed capability token")
        unsigned = ".".join(parts[:2])
        expected = _b64(hmac.new(self._secret, unsigned.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(expected, parts[2]):
            raise TokenError("invalid capability token signature")
        try:
            header = _decode(parts[0])
            claims = CapabilityClaims.model_validate(_decode(parts[1]))
        except (ValueError, ValidationError, json.JSONDecodeError) as exc:
            raise TokenError("invalid capability token payload") from exc
        if header != {"alg": "HS256", "typ": "SCCT"}:
            raise TokenError("unsupported capability token header")
        if claims.issuer != self._issuer or claims.audience != self._audience:
            raise TokenError("capability token issuer or audience mismatch")
        if claims.expires_at <= int(self._clock().timestamp()):
            raise TokenError("capability token expired")
        return claims


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _encode(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return _b64(encoded)


def _decode(value: str) -> Any:
    padding = "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode(value + padding))
