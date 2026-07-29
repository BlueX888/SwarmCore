from unittest.mock import AsyncMock

import pytest
from swarmcore_runtime_temporal.scheduler import NodeState
from swarmcore_runtime_temporal.workflow import SwarmRunWorkflow


@pytest.mark.asyncio
async def test_router_records_empty_output_for_unselected_branch(monkeypatch) -> None:
    runtime = SwarmRunWorkflow()
    runtime._states = {
        "review-router": NodeState.SUCCEEDED,
        "manual-review": NodeState.PENDING,
        "auto-continue": NodeState.PENDING,
    }
    runtime._outputs = {}
    runtime._project = AsyncMock()
    monkeypatch.setattr(
        "swarmcore_runtime_temporal.workflow.workflow.patched",
        lambda _: True,
    )

    await runtime._apply_router_selection(
        {
            "key": "review-router",
            "config": {
                "routes": [{"target": "manual-review"}],
                "default": "auto-continue",
            },
        },
        {"selected": "auto-continue"},
    )

    assert runtime._states["manual-review"] == NodeState.SKIPPED
    assert runtime._outputs["manual-review"] == {}
    runtime._project.assert_awaited_once_with(
        "task.skipped",
        {"nodeKey": "manual-review", "route": "review-router"},
    )
