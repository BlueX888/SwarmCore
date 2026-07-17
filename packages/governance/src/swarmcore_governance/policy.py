from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class PolicyError(RuntimeError):
    """A policy decision could not be obtained or enforced."""


class PolicyDenied(PolicyError):
    pass


class PolicySubject(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    id: str
    tenant_id: str = Field(alias="tenantId")
    roles: tuple[str, ...] = ()
    scopes: tuple[str, ...] = ()


class PolicyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    subject: PolicySubject
    action: str
    resource: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)


class PolicyObligations(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    require_approval: bool = Field(default=False, alias="requireApproval")
    allowed_egress: tuple[str, ...] = Field(default=(), alias="allowedEgress")
    max_duration_seconds: int | None = Field(
        default=None, alias="maxDurationSeconds", ge=1, le=86_400
    )
    redact_fields: tuple[str, ...] = Field(default=(), alias="redactFields")
    max_bytes: int | None = Field(default=None, alias="maxBytes", ge=1)


class PolicyDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    allow: bool
    obligations: PolicyObligations = Field(default_factory=PolicyObligations)
    policy_revision: str = Field(alias="policyRevision", min_length=1)
    reason: str | None = None

    def enforce(self) -> PolicyDecision:
        if not self.allow:
            raise PolicyDenied(self.reason or "policy denied the action")
        return self


class PolicyEngine(Protocol):
    async def evaluate(self, request: PolicyRequest) -> PolicyDecision: ...


@dataclass(frozen=True)
class RolePolicyEngine:
    """Deterministic local policy used by tests and the local development profile."""

    revision: str = "local-policy:v1"
    emergency_denies: frozenset[str] = frozenset()

    _ROLE_ACTIONS: ClassVar[dict[str, frozenset[str]]] = {
        "tenant_admin": frozenset({"*"}),
        "project_admin": frozenset(
            {
                "strategy.*",
                "run.*",
                "approval.*",
                "artifact.*",
                "audit.read",
                "budget.*",
                "webhook.*",
            }
        ),
        "strategy_author": frozenset({"strategy.*"}),
        "run_operator": frozenset({"run.*"}),
        "approver": frozenset({"approval.decide"}),
        "auditor": frozenset({"run.read", "artifact.read", "audit.read"}),
        "viewer": frozenset({"run.read", "artifact.read"}),
        "workload": frozenset(
            {
                "tool.execute",
                "tool.compensate",
                "model.invoke",
                "secret.read",
                "artifact.*",
                "sandbox.execute",
                "webhook.deliver",
            }
        ),
    }

    async def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        if request.action in self.emergency_denies or "*" in self.emergency_denies:
            return PolicyDecision(
                allow=False,
                policyRevision=self.revision,
                reason="emergency deny is active",
            )
        allow = any(
            _matches(request.action, granted)
            for role in request.subject.roles
            for granted in self._ROLE_ACTIONS.get(role, ())
        ) or any(_matches(request.action, scope) for scope in request.subject.scopes)
        obligations: dict[str, Any] = {}
        risk = request.resource.get("risk")
        if request.action == "tool.execute" and risk in {"HIGH", "CRITICAL"}:
            obligations["requireApproval"] = True
        if request.action == "sandbox.execute":
            obligations["maxDurationSeconds"] = 300
            obligations["allowedEgress"] = request.resource.get("allowedEgress", [])
        return PolicyDecision(
            allow=allow,
            obligations=PolicyObligations.model_validate(obligations),
            policyRevision=self.revision,
            reason=None if allow else "role or scope does not grant the action",
        )


class OpaPolicyEngine:
    """Fail-closed OPA Data API adapter with strict obligation validation."""

    def __init__(self, url: str, *, timeout_seconds: float = 2.0) -> None:
        self._url = url.rstrip("/")
        self._timeout = timeout_seconds

    async def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        payload = json.dumps(
            {"input": request.model_dump(mode="json", by_alias=True)},
            separators=(",", ":"),
        ).encode()
        try:
            raw = await asyncio.to_thread(self._post, payload)
            document = json.loads(raw)
            result = document.get("result")
            if not isinstance(result, dict):
                raise PolicyError("OPA returned no decision")
            return PolicyDecision.model_validate(result)
        except PolicyError:
            raise
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, ValidationError) as exc:
            raise PolicyError(f"OPA decision failed: {type(exc).__name__}") from exc

    def _post(self, payload: bytes) -> bytes:
        request = Request(
            self._url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self._timeout) as response:
            return cast(bytes, response.read(1_048_576))


def redact_policy_log(request: PolicyRequest, decision: PolicyDecision) -> dict[str, Any]:
    resource = dict(request.resource)
    context = dict(request.context)
    for field in decision.obligations.redact_fields:
        if field in resource:
            resource[field] = "[REDACTED]"
        if field in context:
            context[field] = "[REDACTED]"
    return {
        "subjectId": request.subject.id,
        "tenantId": request.subject.tenant_id,
        "action": request.action,
        "resource": resource,
        "context": context,
        "allow": decision.allow,
        "policyRevision": decision.policy_revision,
        "reason": decision.reason,
    }


def _matches(action: str, grant: str) -> bool:
    return (
        grant == "*"
        or action == grant
        or (grant.endswith(".*") and action.startswith(grant[:-1]))
    )
