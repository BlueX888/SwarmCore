from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from swarmcore_application import (
    AgentRuntimeStatus,
    CapabilityCenterService,
    CapabilityPresetService,
    CapabilityReadinessService,
    ModelRuntimeStatus,
    ProjectConfigurationService,
    ToolRuntimeStatus,
)
from swarmcore_registry import builtin_registry


class NotReadyRuntime:
    async def inspect_tool(self, **_: object) -> ToolRuntimeStatus:
        return ToolRuntimeStatus(False, False)

    async def inspect_model(self, **_: object) -> ModelRuntimeStatus:
        return ModelRuntimeStatus(False, False, False)

    async def inspect_agent(self, **_: object) -> AgentRuntimeStatus:
        return AgentRuntimeStatus(False)


class CapturingConfigurations:
    def __init__(self) -> None:
        self.arguments: dict[str, Any] | None = None

    async def create(self, session: object, **arguments: Any) -> Any:
        del session
        self.arguments = arguments
        return SimpleNamespace(**arguments)


def _center() -> CapabilityCenterService:
    runtime = NotReadyRuntime()
    return CapabilityCenterService(
        builtin_registry(),
        CapabilityReadinessService(tools=runtime, models=runtime, agents=runtime),
    )


@pytest.mark.parametrize(
    "parameters",
    [
        {"apiKey": "plain-text"},
        {"nested": {"access_token": "plain-text"}},
        {"items": [{"password": "plain-text"}]},
        {"authorization": "Bearer plain-text"},
    ],
)
def test_preset_rejects_secret_fields(parameters: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="forbidden secret field"):
        CapabilityPresetService.validate_parameters(parameters)


def test_preset_allows_secret_references_but_not_empty_parameters() -> None:
    CapabilityPresetService.validate_parameters(
        {"credentialRef": "secret://project/provider"}
    )
    with pytest.raises(ValueError, match="cannot be empty"):
        CapabilityPresetService.validate_parameters({})


@pytest.mark.asyncio
async def test_not_ready_capability_can_still_own_a_preset() -> None:
    configurations = CapturingConfigurations()
    service = CapabilityPresetService(
        _center(), cast(ProjectConfigurationService, configurations)
    )
    await service.create(
        object(),  # type: ignore[arg-type]
        tenant_id=uuid4(),
        project_id=uuid4(),
        environment="development",
        name="演示预设",
        capability_ref="tool://search@1",
        parameters={"query": "swarm"},
        actor="test",
    )
    assert configurations.arguments is not None
    assert configurations.arguments["source_ref"] == "tool://search@1"
    assert configurations.arguments["configuration"] == {"query": "swarm"}
