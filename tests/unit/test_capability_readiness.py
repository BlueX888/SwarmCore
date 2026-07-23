from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

import pytest
from swarmcore_application import (
    AgentRuntimeStatus,
    CapabilityReadinessService,
    ModelRuntimeStatus,
    ToolRuntimeStatus,
)
from swarmcore_domain import CapabilityReadinessStatus, ReadinessReasonCode
from swarmcore_registry import (
    AgentRegistration,
    ModelRegistration,
    RegistrySnapshot,
    ToolRegistration,
    ToolRisk,
    builtin_registry,
)


@dataclass
class RuntimePorts:
    tool: ToolRuntimeStatus = field(
        default_factory=lambda: ToolRuntimeStatus(True, True)
    )
    model: ModelRuntimeStatus = field(
        default_factory=lambda: ModelRuntimeStatus(True, True, True)
    )
    agent: AgentRuntimeStatus = field(
        default_factory=lambda: AgentRuntimeStatus(True)
    )
    calls: int = 0

    async def inspect_tool(self, **_: object) -> ToolRuntimeStatus:
        self.calls += 1
        return self.tool

    async def inspect_model(self, **_: object) -> ModelRuntimeStatus:
        self.calls += 1
        return self.model

    async def inspect_agent(self, **_: object) -> AgentRuntimeStatus:
        self.calls += 1
        return self.agent


def _service(
    ports: RuntimePorts, *, clock: list[float] | None = None
) -> CapabilityReadinessService:
    return CapabilityReadinessService(
        tools=ports,
        models=ports,
        agents=ports,
        ttl_seconds=10,
        clock=(lambda: clock[0]) if clock is not None else (lambda: 0),
    )


async def _project(
    service: CapabilityReadinessService,
    registry: RegistrySnapshot,
    *,
    tenant_id: UUID | None = None,
    project_id: UUID | None = None,
    environment: str = "development",
):
    return await service.project(
        tenant_id=tenant_id or uuid4(),
        project_id=project_id or uuid4(),
        environment=environment,
        registry=registry,
    )


def _codes(summary: Any) -> set[ReadinessReasonCode]:
    return {reason.code for reason in summary.readiness.reasons}


@pytest.mark.asyncio
async def test_registered_pack_tools_without_executors_are_not_ready() -> None:
    ports = RuntimePorts(tool=ToolRuntimeStatus(False, False))
    summaries = await _project(_service(ports), builtin_registry())
    contract_tool = next(
        item
        for item in summaries
        if item.ref == "tool://contract/cross-file-consistency@1"
    )
    assert contract_tool.readiness.status is CapabilityReadinessStatus.NOT_READY
    assert _codes(contract_tool) == {ReadinessReasonCode.EXECUTOR_MISSING}


@pytest.mark.asyncio
async def test_model_secret_endpoint_environment_and_policy_all_gate_readiness() -> None:
    ports = RuntimePorts(
        model=ModelRuntimeStatus(
            route_registered=True,
            secret_available=False,
            endpoint_healthy=False,
            environment_allowed=False,
            policy_allowed=False,
        )
    )
    registry = RegistrySnapshot.create(
        models=(
            ModelRegistration(
                ref="model://only@1",
                version="1",
                runtime="agno",
                providerModel="provider/model",
                environments=("production",),
            ),
        )
    )
    summary = (await _project(_service(ports), registry))[0]
    assert _codes(summary) == {
        ReadinessReasonCode.SECRET_MISSING,
        ReadinessReasonCode.HEALTH_CHECK_FAILED,
        ReadinessReasonCode.ENVIRONMENT_NOT_ALLOWED,
        ReadinessReasonCode.POLICY_DENIED,
    }


@pytest.mark.asyncio
async def test_unrouted_models_are_omitted_from_capability_catalog() -> None:
    registry = RegistrySnapshot.create(
        models=(
            ModelRegistration(
                ref="model://routed@1",
                version="1",
                runtime="agno",
                providerModel="provider/routed",
                environments=("development",),
            ),
            ModelRegistration(
                ref="model://unrouted@1",
                version="1",
                runtime="agno",
                providerModel="provider/unrouted",
                environments=("development",),
            ),
        )
    )

    class SelectiveModelPorts(RuntimePorts):
        async def inspect_model(self, **kwargs: object) -> ModelRuntimeStatus:
            self.calls += 1
            registration = kwargs["registration"]
            assert isinstance(registration, ModelRegistration)
            if registration.ref.endswith("unrouted@1"):
                return ModelRuntimeStatus(False, False, False)
            return ModelRuntimeStatus(True, True, True)

    summaries = await _project(_service(SelectiveModelPorts()), registry)
    assert [item.ref for item in summaries] == ["model://routed@1"]


@pytest.mark.asyncio
async def test_unreachable_model_gateway_keeps_models_visible_as_unhealthy() -> None:
    ports = RuntimePorts(
        model=ModelRuntimeStatus(
            route_registered=False,
            secret_available=False,
            endpoint_healthy=False,
            inspected=False,
        )
    )
    registry = RegistrySnapshot.create(
        models=(
            ModelRegistration(
                ref="model://offline@1",
                version="1",
                runtime="agno",
                providerModel="provider/model",
                environments=("development",),
            ),
        )
    )
    summary = (await _project(_service(ports), registry))[0]
    assert summary.ref == "model://offline@1"
    assert _codes(summary) == {ReadinessReasonCode.HEALTH_CHECK_FAILED}


@pytest.mark.asyncio
async def test_agent_still_depends_on_unrouted_model_summary() -> None:
    ports = RuntimePorts(
        model=ModelRuntimeStatus(False, False, False),
        agent=AgentRuntimeStatus(True),
    )
    registry = RegistrySnapshot.create(
        agents=(
            AgentRegistration(
                ref="agent://needs-model@1",
                version="1",
                role="needs-model",
                instructions="needs a model",
                model="model://missing-route@1",
                tools=(),
            ),
        ),
        models=(
            ModelRegistration(
                ref="model://missing-route@1",
                version="1",
                runtime="agno",
                providerModel="provider/model",
                environments=("development",),
            ),
        ),
    )
    summaries = await _project(_service(ports), registry)
    assert [item.ref for item in summaries] == ["agent://needs-model@1"]
    agent = summaries[0]
    assert ReadinessReasonCode.DEPENDENCY_NOT_READY in _codes(agent)
    assert {reason.dependency_ref for reason in agent.readiness.reasons} == {
        "model://missing-route@1"
    }


@pytest.mark.asyncio
async def test_agent_aggregates_adapter_model_and_tool_readiness() -> None:
    ports = RuntimePorts(
        tool=ToolRuntimeStatus(False, False),
        model=ModelRuntimeStatus(False, False, False),
        agent=AgentRuntimeStatus(False),
    )
    summaries = await _project(_service(ports), builtin_registry())
    agent = next(item for item in summaries if item.ref == "agent://builtin/researcher@1")
    assert _codes(agent) == {
        ReadinessReasonCode.ADAPTER_MISSING,
        ReadinessReasonCode.DEPENDENCY_NOT_READY,
    }
    assert {reason.dependency_ref for reason in agent.readiness.reasons} >= {
        "model://general@1",
        "tool://search@1",
    }
    assert agent.input_schema is not None
    assert agent.input_schema["required"] == ["topic"]
    assert agent.input_schema["properties"]["maxSources"]["default"] == 8


@pytest.mark.asyncio
async def test_invalid_schema_prevents_tool_readiness() -> None:
    registry = RegistrySnapshot.create(
        tools=(
            ToolRegistration(
                ref="tool://invalid@1",
                version="1",
                operation="invalid",
                description="Invalid schema",
                risk=ToolRisk.LOW,
                inputSchema={"type": "not-a-json-schema-type"},
                outputSchema={"type": "object"},
                idempotent=True,
                sideEffecting=False,
                recoveryPolicy="idempotent",
            ),
        )
    )
    summary = (await _project(_service(RuntimePorts()), registry))[0]
    assert _codes(summary) == {ReadinessReasonCode.SCHEMA_INVALID}


@pytest.mark.asyncio
async def test_agent_dependency_cycle_is_reported() -> None:
    first = AgentRegistration(
        ref="agent://first@1",
        version="1",
        role="first",
        instructions="first",
        model="model://ready@1",
        tools=("agent://second@1",),
    )
    second = AgentRegistration(
        ref="agent://second@1",
        version="1",
        role="second",
        instructions="second",
        model="model://ready@1",
        tools=("agent://first@1",),
    )
    model = ModelRegistration(
        ref="model://ready@1",
        version="1",
        runtime="agno",
        providerModel="provider/model",
        environments=("development",),
    )
    summaries = await _project(
        _service(RuntimePorts()),
        RegistrySnapshot.create(agents=(first, second), models=(model,)),
    )
    assert ReadinessReasonCode.DEPENDENCY_CYCLE in _codes(summaries[0])


@pytest.mark.asyncio
async def test_cache_is_scoped_and_expires_by_tenant_project_environment_and_snapshot() -> None:
    ports = RuntimePorts()
    clock = [0.0]
    service = _service(ports, clock=clock)
    registry = RegistrySnapshot.create(
        models=(
            ModelRegistration(
                ref="model://ready@1",
                version="1",
                runtime="agno",
                providerModel="provider/model",
                environments=("development", "test"),
            ),
        )
    )
    tenant_id, project_id = uuid4(), uuid4()
    await _project(
        service, registry, tenant_id=tenant_id, project_id=project_id
    )
    await _project(
        service, registry, tenant_id=tenant_id, project_id=project_id
    )
    assert ports.calls == 1
    await _project(
        service,
        registry,
        tenant_id=tenant_id,
        project_id=project_id,
        environment="test",
    )
    assert ports.calls == 2
    clock[0] = 11.0
    await _project(
        service, registry, tenant_id=tenant_id, project_id=project_id
    )
    assert ports.calls == 3


@pytest.mark.asyncio
async def test_cache_ttl_starts_after_a_slow_readiness_projection_finishes() -> None:
    clock = [0.0]

    class SlowRuntimePorts(RuntimePorts):
        async def inspect_model(self, **_: object) -> ModelRuntimeStatus:
            self.calls += 1
            clock[0] += 11
            return self.model

    ports = SlowRuntimePorts()
    service = _service(ports, clock=clock)
    registry = RegistrySnapshot.create(
        models=(
            ModelRegistration(
                ref="model://slow@1",
                version="1",
                runtime="agno",
                providerModel="provider/model",
                environments=("development",),
            ),
        )
    )
    tenant_id, project_id = uuid4(), uuid4()

    await _project(service, registry, tenant_id=tenant_id, project_id=project_id)
    await _project(service, registry, tenant_id=tenant_id, project_id=project_id)

    assert ports.calls == 1
