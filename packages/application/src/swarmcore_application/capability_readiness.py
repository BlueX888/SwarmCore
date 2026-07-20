from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from jsonschema import Draft202012Validator, SchemaError
from swarmcore_domain import (
    CapabilityKind,
    CapabilityReadiness,
    CapabilityReadinessStatus,
    CapabilitySummary,
    ReadinessReason,
    ReadinessReasonCode,
)
from swarmcore_registry import (
    AgentRegistration,
    ModelRegistration,
    RegistrySnapshot,
    ToolRegistration,
)


@dataclass(frozen=True, slots=True)
class ToolRuntimeStatus:
    executor_registered: bool
    healthy: bool
    environment_allowed: bool = True
    policy_allowed: bool = True


@dataclass(frozen=True, slots=True)
class ModelRuntimeStatus:
    route_registered: bool
    secret_available: bool
    endpoint_healthy: bool
    environment_allowed: bool = True
    policy_allowed: bool = True


@dataclass(frozen=True, slots=True)
class AgentRuntimeStatus:
    adapter_available: bool
    environment_allowed: bool = True
    policy_allowed: bool = True


class ToolReadinessPort(Protocol):
    async def inspect_tool(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        registration: ToolRegistration,
    ) -> ToolRuntimeStatus: ...


class ModelReadinessPort(Protocol):
    async def inspect_model(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        registration: ModelRegistration,
    ) -> ModelRuntimeStatus: ...


class AgentReadinessPort(Protocol):
    async def inspect_agent(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        registration: AgentRegistration,
    ) -> AgentRuntimeStatus: ...


@dataclass(frozen=True, slots=True)
class _CacheKey:
    tenant_id: UUID
    project_id: UUID
    environment: str
    snapshot_id: str


class CapabilityReadinessService:
    def __init__(
        self,
        *,
        tools: ToolReadinessPort,
        models: ModelReadinessPort,
        agents: AgentReadinessPort,
        ttl_seconds: float = 15.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("readiness cache TTL must be positive")
        self._tools = tools
        self._models = models
        self._agents = agents
        self._ttl_seconds = ttl_seconds
        self._clock = clock
        self._cache: dict[_CacheKey, tuple[float, tuple[CapabilitySummary, ...]]] = {}

    async def project(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        registry: RegistrySnapshot,
    ) -> tuple[CapabilitySummary, ...]:
        clean_environment = environment.strip()
        if not clean_environment:
            raise ValueError("environment is required")
        key = _CacheKey(tenant_id, project_id, clean_environment, registry.snapshot_id)
        now = self._clock()
        cached = self._cache.get(key)
        if cached is not None and cached[0] > now:
            return cached[1]

        tools = {
            item.ref: await self._tool_summary(
                tenant_id, project_id, clean_environment, item
            )
            for item in registry.tools
        }
        models = {
            item.ref: await self._model_summary(
                tenant_id, project_id, clean_environment, item
            )
            for item in registry.models
        }
        agent_items: list[CapabilitySummary] = []
        for item in registry.agents:
            agent_items.append(
                await self._agent_summary(
                    tenant_id,
                    project_id,
                    clean_environment,
                    item,
                    registry,
                    models,
                    tools,
                    visiting=(),
                )
            )
        agents = tuple(agent_items)
        result = (*agents, *models.values(), *tools.values())
        self._cache[key] = (now + self._ttl_seconds, result)
        return result

    async def _tool_summary(
        self,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        registration: ToolRegistration,
    ) -> CapabilitySummary:
        reasons = self._schema_reasons(
            registration.ref, registration.input_schema, registration.output_schema
        )
        status = await self._tools.inspect_tool(
            tenant_id=tenant_id,
            project_id=project_id,
            environment=environment,
            registration=registration,
        )
        if not status.executor_registered:
            reasons.append(self._reason(ReadinessReasonCode.EXECUTOR_MISSING))
        elif not status.healthy:
            reasons.append(self._reason(ReadinessReasonCode.HEALTH_CHECK_FAILED))
        self._append_scope_reasons(reasons, status.environment_allowed, status.policy_allowed)
        return CapabilitySummary(
            ref=registration.ref,
            kind=CapabilityKind.TOOL,
            name=registration.ref.split("/")[-1].split("@")[0],
            description=registration.description,
            risk=registration.risk.value,
            inputSchema=registration.input_schema,
            outputSchema=registration.output_schema,
            readiness=self._readiness(reasons),
        )

    async def _model_summary(
        self,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        registration: ModelRegistration,
    ) -> CapabilitySummary:
        reasons: list[ReadinessReason] = []
        if environment not in registration.environments:
            reasons.append(self._reason(ReadinessReasonCode.ENVIRONMENT_NOT_ALLOWED))
        status = await self._models.inspect_model(
            tenant_id=tenant_id,
            project_id=project_id,
            environment=environment,
            registration=registration,
        )
        if not status.route_registered:
            reasons.append(self._reason(ReadinessReasonCode.MODEL_ROUTE_MISSING))
        if not status.secret_available:
            reasons.append(self._reason(ReadinessReasonCode.SECRET_MISSING))
        if not status.endpoint_healthy:
            reasons.append(self._reason(ReadinessReasonCode.HEALTH_CHECK_FAILED))
        self._append_scope_reasons(reasons, status.environment_allowed, status.policy_allowed)
        return CapabilitySummary(
            ref=registration.ref,
            kind=CapabilityKind.MODEL,
            name=registration.ref.split("/")[-1].split("@")[0],
            description=f"Model route for {registration.provider_model}",
            readiness=self._readiness(reasons),
        )

    async def _agent_summary(
        self,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        registration: AgentRegistration,
        registry: RegistrySnapshot,
        models: dict[str, CapabilitySummary],
        tools: dict[str, CapabilitySummary],
        *,
        visiting: tuple[str, ...],
    ) -> CapabilitySummary:
        reasons = self._schema_reasons(
            registration.ref, registration.input_schema, registration.output_schema
        )
        if registration.ref in visiting or self._has_agent_cycle(
            registration, registry, visiting
        ):
            reasons.append(self._reason(ReadinessReasonCode.DEPENDENCY_CYCLE))
        status = await self._agents.inspect_agent(
            tenant_id=tenant_id,
            project_id=project_id,
            environment=environment,
            registration=registration,
        )
        if not status.adapter_available:
            reasons.append(self._reason(ReadinessReasonCode.ADAPTER_MISSING))
        self._append_scope_reasons(reasons, status.environment_allowed, status.policy_allowed)
        model = self._lookup_summary(registration.model, models, registry.resolve_model)
        self._append_dependency(reasons, registration.model, model)
        for tool_ref in registration.tools:
            tool = self._lookup_summary(tool_ref, tools, registry.resolve_tool)
            self._append_dependency(reasons, tool_ref, tool)
        return CapabilitySummary(
            ref=registration.ref,
            kind=CapabilityKind.AGENT,
            name=registration.role,
            description=registration.instructions,
            inputSchema=registration.input_schema,
            outputSchema=registration.output_schema,
            readiness=self._readiness(reasons),
        )

    @classmethod
    def _has_agent_cycle(
        cls,
        registration: AgentRegistration,
        registry: RegistrySnapshot,
        visiting: tuple[str, ...],
    ) -> bool:
        path = (*visiting, registration.ref)
        for reference in (registration.model, *registration.tools):
            dependency = registry.resolve_agent(reference)
            if dependency is None:
                continue
            if dependency.ref in path or cls._has_agent_cycle(dependency, registry, path):
                return True
        return False

    @staticmethod
    def _lookup_summary(
        reference: str,
        summaries: dict[str, CapabilitySummary],
        resolver: Callable[[str], ModelRegistration | ToolRegistration | None],
    ) -> CapabilitySummary | None:
        resolved = resolver(reference)
        if resolved is None:
            return None
        return summaries.get(resolved.ref)

    @classmethod
    def _append_dependency(
        cls,
        reasons: list[ReadinessReason],
        reference: str,
        summary: CapabilitySummary | None,
    ) -> None:
        if summary is None or summary.readiness.status is CapabilityReadinessStatus.NOT_READY:
            reasons.append(
                cls._reason(ReadinessReasonCode.DEPENDENCY_NOT_READY, dependency_ref=reference)
            )

    @staticmethod
    def _schema_reasons(ref: str, *schemas: dict[str, object] | None) -> list[ReadinessReason]:
        for schema in schemas:
            if schema is None:
                continue
            try:
                Draft202012Validator.check_schema(schema)
            except SchemaError:
                return [
                    CapabilityReadinessService._reason(
                        ReadinessReasonCode.SCHEMA_INVALID, dependency_ref=ref
                    )
                ]
        return []

    @staticmethod
    def _append_scope_reasons(
        reasons: list[ReadinessReason], environment_allowed: bool, policy_allowed: bool
    ) -> None:
        if not environment_allowed:
            reasons.append(
                CapabilityReadinessService._reason(
                    ReadinessReasonCode.ENVIRONMENT_NOT_ALLOWED
                )
            )
        if not policy_allowed:
            reasons.append(
                CapabilityReadinessService._reason(ReadinessReasonCode.POLICY_DENIED)
            )

    @staticmethod
    def _readiness(reasons: list[ReadinessReason]) -> CapabilityReadiness:
        unique = tuple(dict.fromkeys(reasons))
        return CapabilityReadiness.not_ready(*unique) if unique else CapabilityReadiness.ready()

    @staticmethod
    def _reason(
        code: ReadinessReasonCode, *, dependency_ref: str | None = None
    ) -> ReadinessReason:
        messages = {
            ReadinessReasonCode.EXECUTOR_MISSING: "No executor is registered.",
            ReadinessReasonCode.ADAPTER_MISSING: "The agent adapter is unavailable.",
            ReadinessReasonCode.MODEL_ROUTE_MISSING: "No provider route is configured.",
            ReadinessReasonCode.SECRET_MISSING: "The provider credential cannot be leased.",
            ReadinessReasonCode.DEPENDENCY_NOT_READY: "A required capability is not ready.",
            ReadinessReasonCode.DEPENDENCY_CYCLE: "A capability dependency cycle was detected.",
            ReadinessReasonCode.HEALTH_CHECK_FAILED: "The runtime health check failed.",
            ReadinessReasonCode.ENVIRONMENT_NOT_ALLOWED: "The environment is not allowed.",
            ReadinessReasonCode.CAPABILITY_PACK_DISABLED: "The capability pack is disabled.",
            ReadinessReasonCode.SCHEMA_INVALID: "The declared schema is invalid.",
            ReadinessReasonCode.POLICY_DENIED: "Policy does not allow this capability.",
        }
        return ReadinessReason(
            code=code, message=messages[code], dependencyRef=dependency_ref
        )
