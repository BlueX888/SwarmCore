from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from swarmcore_application import (
    AgentRuntimeStatus,
    CapabilityCenterService,
    CapabilityReadinessService,
    ModelRuntimeStatus,
    ProjectConfigurationService,
    RunService,
    ToolRuntimeStatus,
)
from swarmcore_compiler import Compiler
from swarmcore_registry import builtin_registry
from swarmcore_spec import SwarmStrategy


class ReadyRuntime:
    async def inspect_tool(self, **_: object) -> ToolRuntimeStatus:
        return ToolRuntimeStatus(True, True)

    async def inspect_model(self, **_: object) -> ModelRuntimeStatus:
        return ModelRuntimeStatus(True, True, True)

    async def inspect_agent(self, **_: object) -> AgentRuntimeStatus:
        return AgentRuntimeStatus(True)


class MissingToolRuntime(ReadyRuntime):
    async def inspect_tool(self, **_: object) -> ToolRuntimeStatus:
        return ToolRuntimeStatus(False, False)


class CountingRuntime(ReadyRuntime):
    def __init__(self) -> None:
        self.tool_calls = 0
        self.model_calls = 0
        self.agent_calls = 0

    async def inspect_tool(self, **kwargs: object) -> ToolRuntimeStatus:
        self.tool_calls += 1
        return await super().inspect_tool(**kwargs)

    async def inspect_model(self, **kwargs: object) -> ModelRuntimeStatus:
        self.model_calls += 1
        return await super().inspect_model(**kwargs)

    async def inspect_agent(self, **kwargs: object) -> AgentRuntimeStatus:
        self.agent_calls += 1
        return await super().inspect_agent(**kwargs)


def _center(runtime: ReadyRuntime) -> CapabilityCenterService:
    registry = builtin_registry()
    readiness = CapabilityReadinessService(
        tools=runtime,
        models=runtime,
        agents=runtime,
    )
    return CapabilityCenterService(registry, readiness)


class CapturingRuns:
    def __init__(self) -> None:
        self.arguments: dict[str, Any] | None = None

    async def create_inline(self, session: object, **arguments: Any):
        del session
        self.arguments = arguments
        return (
            SimpleNamespace(id=uuid4(), status="PENDING", plan_hash="plan"),
            SimpleNamespace(id=uuid4(), status="PENDING"),
        )


class ProjectAgents:
    def __init__(self, row: SimpleNamespace) -> None:
        self.row = row

    async def list(self, session: object, **_: Any):
        del session
        return [self.row], 1

    async def get(self, session: object, **_: Any):
        del session
        return self.row


@pytest.mark.asyncio
async def test_capability_center_projects_all_registry_resources() -> None:
    center = _center(ReadyRuntime())
    items = await center.list(
        tenant_id=uuid4(), project_id=uuid4(), environment="development"
    )
    assert {item.kind.value for item in items} == {"agent", "model", "tool"}
    assert center.registry_snapshot_id == builtin_registry().snapshot_id


@pytest.mark.parametrize(
    ("capability_ref", "expected_type"),
    [
        ("tool://search@1", "tool"),
        ("agent://builtin/researcher@1", "agent"),
        ("model://general@1", "agent"),
    ],
)
@pytest.mark.asyncio
async def test_direct_capability_builds_compilable_single_node_spec(
    capability_ref: str, expected_type: str
) -> None:
    center = _center(ReadyRuntime())
    summaries = await center.list(
        tenant_id=uuid4(), project_id=uuid4(), environment="development"
    )
    summary = next(item for item in summaries if item.ref == capability_ref)
    raw_spec = center.build_spec(summary, input_data={"query": "swarm"})
    spec = SwarmStrategy.model_validate(raw_spec)
    Compiler().compile(
        spec,
        registry_snapshot=builtin_registry().snapshot_id,
        policy_revision="test",
    )
    assert len(spec.spec.graph.nodes.root) == 1
    assert spec.spec.graph.nodes.root["capability"].type == expected_type


@pytest.mark.asyncio
async def test_not_ready_capability_is_rejected_before_run_creation() -> None:
    center = _center(MissingToolRuntime())
    with pytest.raises(ValueError, match="CAPABILITY_NOT_READY: EXECUTOR_MISSING"):
        await center.run(
            object(),  # type: ignore[arg-type]
            tenant_id=uuid4(),
            project_id=uuid4(),
            environment="development",
            capability_ref="tool://search@1",
            input_data={"query": "swarm"},
            preset_id=None,
            idempotency_key="direct-search",
            initiated_by="test",
            submitted_scopes=(),
            auth_context_hash="test",
        )


@pytest.mark.asyncio
async def test_ready_capability_reuses_inline_run_service() -> None:
    runtime = ReadyRuntime()
    registry = builtin_registry()
    readiness = CapabilityReadinessService(
        tools=runtime, models=runtime, agents=runtime
    )
    runs = CapturingRuns()
    center = CapabilityCenterService(registry, readiness, cast(RunService, runs))
    await center.run(
        object(),  # type: ignore[arg-type]
        tenant_id=uuid4(),
        project_id=uuid4(),
        environment="development",
        capability_ref="tool://search@1",
        input_data={"query": "swarm"},
        preset_id=None,
        idempotency_key="direct-search",
        initiated_by="test",
        submitted_scopes=("run:create",),
        auth_context_hash="context",
    )
    assert runs.arguments is not None
    assert runs.arguments["registry_snapshot"] == registry.snapshot_id
    assert runs.arguments["idempotency_key"] == "direct-search"
    spec = SwarmStrategy.model_validate(runs.arguments["raw_spec"])
    assert spec.spec.graph.nodes.root["capability"].type == "tool"


@pytest.mark.asyncio
async def test_project_agent_is_listed_and_runs_its_inline_agno_definition() -> None:
    runtime = CountingRuntime()
    registry = builtin_registry()
    readiness = CapabilityReadinessService(
        tools=runtime, models=runtime, agents=runtime
    )
    runs = CapturingRuns()
    configuration_id = uuid4()
    row = SimpleNamespace(
        id=configuration_id,
        revision=2,
        name="项目研究员",
        configuration={
            "spec": {
                "agents": {
                    "researcher": {
                        "role": "project-researcher",
                        "instructions": "Research the supplied task.",
                        "model": "model://general@1",
                        "tools": ["tool://search@1"],
                    }
                },
                "graph": {
                    "entrypoint": "researcher",
                    "nodes": {
                        "researcher": {
                            "type": "agent",
                            "agent": "researcher",
                            "dependsOn": [],
                        }
                    },
                },
            }
        },
    )
    center = CapabilityCenterService(
        registry,
        readiness,
        cast(RunService, runs),
        cast(ProjectConfigurationService, ProjectAgents(row)),
    )
    project_ref = center.project_agent_ref(configuration_id, 2)

    items = await center.list(
        tenant_id=uuid4(),
        project_id=uuid4(),
        environment="development",
        session=cast(Any, object()),
    )
    project_agent = next(item for item in items if item.ref == project_ref)
    assert project_agent.name == "项目研究员"
    assert project_agent.source == "project"
    assert project_agent.readiness.status.value == "READY"
    assert runtime.tool_calls == len(registry.tools)
    assert runtime.model_calls == len(registry.models)
    assert runtime.agent_calls == len(registry.agents)

    await center.run(
        cast(Any, object()),
        tenant_id=uuid4(),
        project_id=uuid4(),
        environment="development",
        capability_ref=project_ref,
        input_data={"query": "swarm"},
        preset_id=None,
        idempotency_key="project-agent",
        initiated_by="test",
        submitted_scopes=("run:create",),
        auth_context_hash="context",
    )
    assert runs.arguments is not None
    spec = SwarmStrategy.model_validate(runs.arguments["raw_spec"])
    assert spec.spec.agents["researcher"].role == "project-researcher"
    assert spec.spec.graph.nodes.root["researcher"].type == "agent"
