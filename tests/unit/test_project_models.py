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
    synthesize_project_model_registration,
)
from swarmcore_application.project_models import project_model_capability_summary
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


class UnhealthyModelRuntime(ReadyRuntime):
    async def inspect_model(self, **_: object) -> ModelRuntimeStatus:
        return ModelRuntimeStatus(True, True, False)


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


def test_synthesize_project_model_registration_accepts_uuid_refs() -> None:
    model_id = uuid4()
    registration = synthesize_project_model_registration(f"model://project/{model_id}@2")
    assert registration is not None
    assert registration.ref == f"model://project/{model_id}@2"
    assert registration.provider_model == f"model://project/{model_id}"
    assert synthesize_project_model_registration("model://project/not-a-uuid") is None


def test_project_model_capability_summary_is_ready_when_provider_is_verified() -> None:
    model_id = uuid4()
    summary = project_model_capability_summary(
        logical_model=f"model://project/{model_id}",
        revision=3,
        configuration={
            "providerUrl": "https://api.example.com/v1",
            "modelName": "gpt-4.1-mini",
            "secretRef": "secret://projects/demo/models/x",
            "displayName": "业务模型",
            "connectionVerifiedAt": "2026-08-07T09:45:46.373435+00:00",
        },
    )
    assert summary is not None
    assert summary.ref == f"model://project/{model_id}@3"
    assert summary.name == "业务模型"
    assert summary.source == "project"
    assert summary.readiness.status.value == "READY"


def test_project_model_capability_summary_not_ready_until_connectivity_verified() -> None:
    model_id = uuid4()
    summary = project_model_capability_summary(
        logical_model=f"model://project/{model_id}",
        revision=1,
        configuration={
            "providerUrl": "https://gateway.example.com/v1",
            "modelName": "MiniMax-M2.7-highspeed",
            "secretRef": "secret://projects/demo/models/minimax",
            "displayName": "MiniMax-M2.7-highspeed",
        },
    )
    assert summary is not None
    assert summary.readiness.status.value == "NOT_READY"
    assert any(
        reason.code.value == "HEALTH_CHECK_FAILED" for reason in summary.readiness.reasons
    )


def test_compiler_accepts_project_model_references() -> None:
    model_id = uuid4()
    model_ref = f"model://project/{model_id}@1"
    strategy = SwarmStrategy.model_validate(
        {
            "apiVersion": "swarmcore.io/v1",
            "kind": "SwarmStrategy",
            "metadata": {"name": "project-model"},
            "spec": {
                "inputSchema": {"type": "object"},
                "outputSchema": {
                    "type": "object",
                    "required": ["result"],
                    "properties": {"result": {"type": "object"}},
                    "additionalProperties": False,
                },
                "agents": {
                    "runner": {
                        "role": "runner",
                        "instructions": "Return the result.",
                        "model": model_ref,
                    }
                },
                "graph": {
                    "entrypoint": "runner",
                    "nodes": {"runner": {"type": "agent", "agent": "runner"}},
                    "output": {"result": "{{ tasks.runner.output }}"},
                },
            },
        }
    )
    plan = Compiler().compile(
        strategy, registry_snapshot=builtin_registry().snapshot_id, policy_revision="policy:1"
    )
    assert model_ref in plan.resolved_models
    assert not [item for item in plan.diagnostics if item.code == "UNKNOWN_MODEL"]


@pytest.mark.asyncio
async def test_capability_center_lists_project_runtime_models() -> None:
    model_id = uuid4()
    logical = f"model://project/{model_id}"
    row = SimpleNamespace(
        id=uuid4(),
        revision=1,
        name=f"__runtime_provider__:{logical}",
        source_ref=logical,
        configuration={
            "providerUrl": "https://api.example.com/v1",
            "modelName": "gpt-4.1-mini",
            "secretRef": "secret://projects/demo/models/x",
            "displayName": "业务模型",
            "connectionVerifiedAt": "2026-08-07T09:45:46.373435+00:00",
        },
    )

    class ProjectModels:
        async def list(self, session: object, **kwargs: Any):
            del session
            if kwargs.get("kind").value == "model":
                return [row], 1
            return [], 0

        async def get(self, session: object, **_: Any):
            del session
            return None

    runtime = ReadyRuntime()
    center = CapabilityCenterService(
        builtin_registry(),
        CapabilityReadinessService(tools=runtime, models=runtime, agents=runtime),
        configurations=cast(ProjectConfigurationService, ProjectModels()),
    )
    items = await center.list(
        tenant_id=uuid4(),
        project_id=uuid4(),
        environment="development",
        session=cast(Any, object()),
    )
    project_model = next(item for item in items if item.ref == f"{logical}@1")
    assert project_model.name == "业务模型"
    assert project_model.source == "project"
    assert project_model.readiness.status.value == "READY"


@pytest.mark.asyncio
async def test_verified_runtime_provider_overrides_generic_probe_failure() -> None:
    row = SimpleNamespace(
        id=uuid4(),
        revision=1,
        name="__runtime_provider__:model://general",
        source_ref="model://general",
        configuration={
            "providerUrl": "https://api.example.com/v1",
            "modelName": "provider-model",
            "secretRef": "secret://projects/demo/models/general",
            "connectionVerifiedAt": "2026-07-28T10:00:00+00:00",
        },
    )

    class ProjectModels:
        async def list(self, session: object, **kwargs: Any):
            del session
            return ([row], 1) if kwargs.get("kind").value == "model" else ([], 0)

        async def get(self, session: object, **_: Any):
            del session
            return None

    runtime = UnhealthyModelRuntime()
    runs = CapturingRuns()
    center = CapabilityCenterService(
        builtin_registry(),
        CapabilityReadinessService(tools=runtime, models=runtime, agents=runtime),
        runs=cast(RunService, runs),
        configurations=cast(ProjectConfigurationService, ProjectModels()),
    )

    items = await center.list(
        tenant_id=uuid4(),
        project_id=uuid4(),
        environment="development",
        session=cast(Any, object()),
    )

    general = next(item for item in items if item.ref == "model://general@1")
    researcher = next(item for item in items if item.ref == "agent://builtin/researcher@1")
    assert general.readiness.status.value == "READY"
    assert researcher.readiness.status.value == "READY"

    await center.run(
        cast(Any, object()),
        tenant_id=uuid4(),
        project_id=uuid4(),
        environment="development",
        capability_ref=researcher.ref,
        input_data={"topic": "verified provider"},
        preset_id=None,
        idempotency_key="verified-provider-run",
        initiated_by="test",
        submitted_scopes=("run:create",),
        auth_context_hash="context",
    )
    assert runs.arguments is not None


@pytest.mark.asyncio
async def test_capability_center_falls_back_when_project_config_listing_fails() -> None:
    class BrokenConfigs:
        async def list(self, session: object, **_: Any):
            del session
            raise ValueError("the greenlet library is required to use this function")

        async def get(self, session: object, **_: Any):
            del session
            return None

    runtime = ReadyRuntime()
    center = CapabilityCenterService(
        builtin_registry(),
        CapabilityReadinessService(tools=runtime, models=runtime, agents=runtime),
        configurations=cast(ProjectConfigurationService, BrokenConfigs()),
    )
    items = await center.list(
        tenant_id=uuid4(),
        project_id=uuid4(),
        environment="development",
        session=cast(Any, object()),
    )
    assert items
    assert all(item.source == "system" for item in items)
    assert any(item.ref == "tool://search@1" for item in items)
    search = next(item for item in items if item.ref == "tool://search@1")
    assert search.description == "在已配置的知识源中检索内容。"
