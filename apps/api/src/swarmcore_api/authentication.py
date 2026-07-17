from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import dataclass
from typing import Any, cast
from uuid import UUID

from .settings import Settings


class AuthenticationError(ValueError):
    pass


@dataclass(frozen=True)
class Identity:
    subject_id: str
    tenant_id: UUID
    roles: tuple[str, ...]
    scopes: tuple[str, ...]
    issuer: str
    audience: str
    project_scopes: tuple[tuple[str, tuple[str, ...]], ...] = ()

    def can_access_project(self, project_id: UUID) -> bool:
        return "tenant_admin" in self.roles or any(
            project == str(project_id) for project, _ in self.project_scopes
        )

    def scopes_for(self, project_id: UUID) -> tuple[str, ...]:
        granted = set(self.scopes)
        for project, scopes in self.project_scopes:
            if project == str(project_id):
                granted.update(scopes)
        return tuple(sorted(granted))

    @property
    def context_hash(self) -> str:
        document = {
            "sub": self.subject_id,
            "tenantId": str(self.tenant_id),
            "roles": sorted(self.roles),
            "scopes": sorted(self.scopes),
            "projectScopes": {
                project: sorted(scopes) for project, scopes in sorted(self.project_scopes)
            },
            "iss": self.issuer,
            "aud": self.audience,
        }
        encoded = json.dumps(document, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


class JwtAuthenticator:
    def __init__(self, settings: Settings) -> None:
        if not settings.jwt_issuer or not settings.jwt_jwks_url:
            raise AuthenticationError("JWT issuer and JWKS URL are required")
        if any(
            algorithm.startswith("HS") or algorithm == "none"
            for algorithm in settings.jwt_algorithms
        ):
            raise AuthenticationError("only asymmetric JWT algorithms are allowed")
        self._settings = settings
        try:
            self._jwt = importlib.import_module("jwt")
        except ModuleNotFoundError as exc:
            raise AuthenticationError("JWT support is not installed") from exc
        self._jwks = self._jwt.PyJWKClient(
            settings.jwt_jwks_url, cache_keys=True, lifespan=300
        )

    def authenticate(self, authorization: str) -> Identity:
        if not authorization.startswith("Bearer "):
            raise AuthenticationError("Bearer authentication is required")
        token = authorization.removeprefix("Bearer ").strip()
        try:
            key = self._jwks.get_signing_key_from_jwt(token)
            claims = self._jwt.decode(
                token,
                key.key,
                algorithms=list(self._settings.jwt_algorithms),
                audience=self._settings.jwt_audience,
                issuer=self._settings.jwt_issuer,
                options={
                    "require": [
                        "sub",
                        "tenant_id",
                        "roles",
                        "project_scopes",
                        "exp",
                        "nbf",
                        "iss",
                        "aud",
                    ]
                },
            )
        except self._jwt.PyJWTError as exc:
            raise AuthenticationError("JWT validation failed") from exc
        return _identity_from_claims(cast(dict[str, Any], claims))


def _identity_from_claims(claims: dict[str, Any]) -> Identity:
    roles = claims.get("roles", [])
    scopes = claims.get("scope", claims.get("scopes", []))
    project_scopes = claims.get("project_scopes")
    if isinstance(scopes, str):
        scopes = scopes.split()
    if (
        not isinstance(roles, list)
        or not isinstance(scopes, list)
        or not isinstance(project_scopes, dict)
    ):
        raise AuthenticationError("JWT roles, scopes, and project scopes are invalid")
    try:
        normalized_project_scopes = tuple(
            sorted(
                (
                    str(UUID(str(project_id))),
                    tuple(str(scope) for scope in grants),
                )
                for project_id, grants in project_scopes.items()
                if isinstance(grants, list)
            )
        )
        if len(normalized_project_scopes) != len(project_scopes):
            raise ValueError("project scope grants must be arrays")
        return Identity(
            subject_id=str(claims["sub"]),
            tenant_id=UUID(str(claims["tenant_id"])),
            roles=tuple(str(item) for item in roles),
            scopes=tuple(str(item) for item in scopes),
            project_scopes=normalized_project_scopes,
            issuer=str(claims["iss"]),
            audience=str(claims["aud"]),
        )
    except (KeyError, ValueError) as exc:
        raise AuthenticationError("JWT identity claims are invalid") from exc
