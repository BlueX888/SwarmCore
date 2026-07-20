from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from jsonschema import Draft202012Validator, ValidationError
from pydantic import BaseModel, ConfigDict, Field
from swarmcore_governance import (
    PolicyDenied,
    PolicyEngine,
    PolicyRequest,
    PolicySubject,
    RolePolicyEngine,
    SecretProvider,
    SecretScanner,
    validate_secret_ref,
)
from swarmcore_registry import RegistrySnapshot, ToolRisk

from .tokens import CapabilityTokenIssuer, TokenError


class GatewayError(ValueError):
    pass


class EffectConflict(GatewayError):
    pass


class EffectInProgress(GatewayError):
    pass


class ToolInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    token: str
    effect_id: str = Field(alias="effectId")
    input: dict[str, Any]


class CompensationInvocation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    token: str
    effect_id: str = Field(alias="effectId")
    input: dict[str, Any]


class EffectReservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    owner: bool
    output: dict[str, Any] | None = None


class EffectJournal(Protocol):
    async def reserve(
        self,
        *,
        tenant_id: str,
        project_id: str,
        run_id: str,
        node_key: str,
        tool_ref: str,
        effect_id: str,
        request_hash: str,
    ) -> EffectReservation: ...

    async def complete(
        self,
        *,
        tenant_id: str,
        project_id: str,
        tool_ref: str,
        effect_id: str,
        output: dict[str, Any],
    ) -> None: ...

    async def fail(
        self,
        *,
        tenant_id: str,
        project_id: str,
        tool_ref: str,
        effect_id: str,
        error: str,
    ) -> None: ...


@dataclass(frozen=True)
class AuditEvent:
    type: str
    tenant_id: str
    project_id: str
    run_id: str
    node_key: str
    tool_ref: str
    effect_id: str
    data: dict[str, Any]


class AuditSink(Protocol):
    async def record(self, event: AuditEvent) -> None: ...


class NullAuditSink:
    async def record(self, event: AuditEvent) -> None:
        del event


ToolExecutor = Callable[[dict[str, Any], str], Awaitable[dict[str, Any]]]


@dataclass(frozen=True, slots=True)
class ToolExecutionContext:
    tenant_id: str
    project_id: str
    run_id: str
    node_key: str
    tool_ref: str
    execution_id: str


@runtime_checkable
class ContextualToolExecutor(Protocol):
    async def execute(
        self,
        input_value: dict[str, Any],
        effect_id: str,
        context: ToolExecutionContext,
    ) -> dict[str, Any]: ...


@runtime_checkable
class HealthyToolExecutor(Protocol):
    async def healthy(self) -> bool: ...


class ToolGateway:
    def __init__(
        self,
        registry: RegistrySnapshot,
        tokens: CapabilityTokenIssuer,
        journal: EffectJournal,
        executors: dict[str, ToolExecutor | ContextualToolExecutor],
        audit: AuditSink | None = None,
        policy: PolicyEngine | None = None,
        secrets: SecretProvider | None = None,
    ) -> None:
        self._registry = registry
        self._tokens = tokens
        self._journal = journal
        self._executors = executors
        self._audit = audit or NullAuditSink()
        self._policy = policy or RolePolicyEngine()
        self._secrets = secrets

    async def readiness(self) -> tuple[dict[str, Any], ...]:
        rows: list[dict[str, Any]] = []
        for registration in self._registry.tools:
            executor = self._executors.get(registration.operation)
            healthy = executor is not None
            if isinstance(executor, HealthyToolExecutor):
                healthy = await executor.healthy()
            rows.append(
                {
                    "ref": registration.ref,
                    "operation": registration.operation,
                    "executorRegistered": executor is not None,
                    "healthy": healthy,
                }
            )
        return tuple(rows)

    async def invoke(self, invocation: ToolInvocation) -> dict[str, Any]:
        try:
            claims = self._tokens.verify(invocation.token)
        except TokenError as exc:
            raise GatewayError(str(exc)) from exc
        if claims.action != "tool.execute":
            raise GatewayError("capability action does not allow Tool execution")
        registration = self._registry.resolve_tool(claims.tool_ref)
        if registration is None:
            raise GatewayError("token references an unknown tool")
        if claims.effect_id is not None and claims.effect_id != invocation.effect_id:
            raise GatewayError("effect id is outside the token scope")
        if registration.risk in {ToolRisk.HIGH, ToolRisk.CRITICAL} and not claims.approved:
            raise GatewayError("high-risk tool requires an approved capability")
        policy_request = PolicyRequest(
            subject=PolicySubject(
                id=claims.execution_id,
                tenantId=claims.tenant_id,
                roles=("workload",),
            ),
            action="tool.execute",
            resource={
                "projectId": claims.project_id,
                "tool": registration.ref,
                "risk": registration.risk.value,
            },
            context={"runId": claims.run_id, "nodeKey": claims.node_key},
        )
        try:
            policy_decision = (await self._policy.evaluate(policy_request)).enforce()
        except PolicyDenied as exc:
            await self._audit.record(
                self._event(
                    "policy.denied",
                    claims,
                    invocation.effect_id,
                    {"action": "tool.execute"},
                )
            )
            raise GatewayError(str(exc)) from exc
        if policy_decision.obligations.require_approval and not claims.approved:
            raise GatewayError("runtime policy requires an approved capability")
        try:
            Draft202012Validator(registration.input_schema).validate(invocation.input)
        except ValidationError as exc:
            raise GatewayError(f"tool input schema violation: {exc.message}") from exc

        canonical_input = json.dumps(
            invocation.input, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        request_hash = hashlib.sha256(canonical_input.encode()).hexdigest()
        if claims.approved and claims.canonical_input_hash != request_hash:
            raise GatewayError("approved capability input hash does not match the invocation")
        reservation = await self._journal.reserve(
            tenant_id=claims.tenant_id,
            project_id=claims.project_id,
            run_id=claims.run_id,
            node_key=claims.node_key,
            tool_ref=registration.ref,
            effect_id=invocation.effect_id,
            request_hash=request_hash,
        )
        if not reservation.owner:
            if reservation.output is None:
                raise EffectInProgress("tool effect is already in progress")
            return reservation.output

        try:
            event = self._event("tool.started", claims, invocation.effect_id, {})
            await self._audit.record(event)
            executor = self._executors[registration.operation]
            async with AsyncExitStack() as stack:
                materialized, scanner = await self._materialize_secrets(
                    invocation.input,
                    stack=stack,
                    claims=claims,
                )
                if isinstance(executor, ContextualToolExecutor):
                    content = await executor.execute(
                        materialized,
                        invocation.effect_id,
                        ToolExecutionContext(
                            tenant_id=claims.tenant_id,
                            project_id=claims.project_id,
                            run_id=claims.run_id,
                            node_key=claims.node_key,
                            tool_ref=claims.tool_ref,
                            execution_id=claims.execution_id,
                        ),
                    )
                else:
                    content = await executor(materialized, invocation.effect_id)
                if scanner is not None:
                    scanner.assert_clean(
                        json.dumps(content, ensure_ascii=False, default=str).encode()
                    )
            Draft202012Validator(registration.output_schema).validate(content)
            output = {
                "content": content,
                "tool": registration.ref,
                "effectId": invocation.effect_id,
                "metrics": {"cost_usd": registration.cost_usd},
            }
            await self._journal.complete(
                tenant_id=claims.tenant_id,
                project_id=claims.project_id,
                tool_ref=registration.ref,
                effect_id=invocation.effect_id,
                output=output,
            )
        except Exception as exc:
            await self._journal.fail(
                tenant_id=claims.tenant_id,
                project_id=claims.project_id,
                tool_ref=registration.ref,
                effect_id=invocation.effect_id,
                error=f"{type(exc).__name__}: {exc}"[:2000],
            )
            await self._audit.record(
                self._event(
                    "tool.failed",
                    claims,
                    invocation.effect_id,
                    {"errorType": type(exc).__name__},
                )
            )
            raise
        await self._audit.record(
            self._event(
                "tool.completed",
                claims,
                invocation.effect_id,
                {"costUsd": registration.cost_usd},
            )
        )
        return output

    async def _materialize_secrets(
        self,
        value: dict[str, Any],
        *,
        stack: AsyncExitStack,
        claims: Any,
    ) -> tuple[dict[str, Any], SecretScanner | None]:
        refs = _secret_refs(value)
        if not refs:
            return value, None
        if self._secrets is None:
            raise GatewayError("tool input references a Secret but no provider is configured")
        resolved: dict[str, dict[str, str]] = {}
        all_values: list[str] = []
        for secret_ref in sorted(refs):
            secret_request = PolicyRequest(
                subject=PolicySubject(
                    id=claims.execution_id,
                    tenantId=claims.tenant_id,
                    roles=("workload",),
                ),
                action="secret.read",
                resource={"projectId": claims.project_id, "secretRef": secret_ref},
                context={"runId": claims.run_id},
            )
            decision = (await self._policy.evaluate(secret_request)).enforce()
            lease = await stack.enter_async_context(self._secrets.lease(secret_ref))
            resolved[secret_ref] = dict(lease.values)
            all_values.extend(lease.values.values())
            await self._audit.record(
                self._event(
                    "secret.accessed",
                    claims,
                    "redacted",
                    {"secretRef": secret_ref, "policyRevision": decision.policy_revision},
                )
            )
        return _replace_secret_refs(value, resolved), SecretScanner(all_values)

    async def compensate(self, invocation: CompensationInvocation) -> dict[str, Any]:
        try:
            claims = self._tokens.verify(invocation.token)
        except TokenError as exc:
            raise GatewayError(str(exc)) from exc
        if claims.action != "tool.compensate":
            raise GatewayError("capability action does not allow compensation")
        registration = self._registry.resolve_tool(claims.tool_ref)
        if registration is None or registration.compensation_operation is None:
            raise GatewayError("tool does not declare an automatic compensation")
        request = PolicyRequest(
            subject=PolicySubject(
                id=claims.execution_id,
                tenantId=claims.tenant_id,
                roles=("workload",),
            ),
            action="tool.compensate",
            resource={"projectId": claims.project_id, "tool": registration.ref},
            context={"runId": claims.run_id, "effectId": invocation.effect_id},
        )
        decision = (await self._policy.evaluate(request)).enforce()
        canonical_input = json.dumps(
            invocation.input, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        compensation_effect = f"{invocation.effect_id}:compensation"
        reservation = await self._journal.reserve(
            tenant_id=claims.tenant_id,
            project_id=claims.project_id,
            run_id=claims.run_id,
            node_key=claims.node_key,
            tool_ref=registration.ref,
            effect_id=compensation_effect,
            request_hash=hashlib.sha256(canonical_input.encode()).hexdigest(),
        )
        if not reservation.owner:
            if reservation.output is None:
                raise EffectInProgress("tool compensation is already in progress")
            return reservation.output
        try:
            executor = self._executors[registration.compensation_operation]
            if isinstance(executor, ContextualToolExecutor):
                content = await executor.execute(
                    invocation.input,
                    invocation.effect_id,
                    ToolExecutionContext(
                        tenant_id=claims.tenant_id,
                        project_id=claims.project_id,
                        run_id=claims.run_id,
                        node_key=claims.node_key,
                        tool_ref=claims.tool_ref,
                        execution_id=claims.execution_id,
                    ),
                )
            else:
                content = await executor(invocation.input, invocation.effect_id)
            output = {
                "content": content,
                "tool": registration.ref,
                "effectId": invocation.effect_id,
                "policyRevision": decision.policy_revision,
            }
            await self._journal.complete(
                tenant_id=claims.tenant_id,
                project_id=claims.project_id,
                tool_ref=registration.ref,
                effect_id=compensation_effect,
                output=output,
            )
        except Exception as exc:
            await self._journal.fail(
                tenant_id=claims.tenant_id,
                project_id=claims.project_id,
                tool_ref=registration.ref,
                effect_id=compensation_effect,
                error=f"{type(exc).__name__}: {exc}"[:2000],
            )
            raise
        await self._audit.record(self._event("tool.compensated", claims, invocation.effect_id, {}))
        return output

    @staticmethod
    def _event(event_type: str, claims: Any, effect_id: str, data: dict[str, Any]) -> AuditEvent:
        return AuditEvent(
            type=event_type,
            tenant_id=claims.tenant_id,
            project_id=claims.project_id,
            run_id=claims.run_id,
            node_key=claims.node_key,
            tool_ref=claims.tool_ref,
            effect_id=effect_id,
            data=data,
        )


class InMemoryEffectJournal:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._effects: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    async def reserve(
        self,
        *,
        tenant_id: str,
        project_id: str,
        run_id: str,
        node_key: str,
        tool_ref: str,
        effect_id: str,
        request_hash: str,
    ) -> EffectReservation:
        del run_id, node_key
        key = (tenant_id, project_id, tool_ref, effect_id)
        async with self._lock:
            existing = self._effects.get(key)
            if existing is None:
                self._effects[key] = {"requestHash": request_hash, "status": "PENDING"}
                return EffectReservation(owner=True)
            if existing["requestHash"] != request_hash:
                raise EffectConflict("effect id was reused with different input")
            if existing["status"] == "SUCCEEDED":
                return EffectReservation(owner=False, output=existing["output"])
            if existing["status"] == "FAILED":
                existing["status"] = "PENDING"
                return EffectReservation(owner=True)
            return EffectReservation(owner=False)

    async def complete(
        self,
        *,
        tenant_id: str,
        project_id: str,
        tool_ref: str,
        effect_id: str,
        output: dict[str, Any],
    ) -> None:
        async with self._lock:
            effect = self._effects[(tenant_id, project_id, tool_ref, effect_id)]
            effect.update(status="SUCCEEDED", output=output)

    async def fail(
        self,
        *,
        tenant_id: str,
        project_id: str,
        tool_ref: str,
        effect_id: str,
        error: str,
    ) -> None:
        async with self._lock:
            effect = self._effects[(tenant_id, project_id, tool_ref, effect_id)]
            effect.update(status="FAILED", error=error)


def _secret_refs(value: Any) -> set[str]:
    if isinstance(value, dict):
        refs = {
            validate_secret_ref(str(value["secretRef"])) for key in ("secretRef",) if key in value
        }
        for item in value.values():
            refs.update(_secret_refs(item))
        return refs
    if isinstance(value, list):
        return {ref for item in value for ref in _secret_refs(item)}
    return set()


def _replace_secret_refs(value: Any, resolved: dict[str, dict[str, str]]) -> Any:
    if isinstance(value, dict):
        if set(value) == {"secretRef"}:
            return resolved[str(value["secretRef"])]
        return {key: _replace_secret_refs(item, resolved) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_secret_refs(item, resolved) for item in value]
    return value
