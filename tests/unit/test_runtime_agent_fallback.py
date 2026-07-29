from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from swarmcore_runtime_temporal.workflow import SwarmRunWorkflow


def _node() -> dict[str, object]:
    return {
        "key": "diagnose",
        "type": "agent",
        "dependencies": [],
        "config": {"agent": "primary", "fallbackAgent": "standby"},
    }


@pytest.mark.asyncio
async def test_agent_success_records_that_fallback_was_not_used() -> None:
    workflow = SwarmRunWorkflow()
    workflow._project = AsyncMock()  # type: ignore[method-assign]
    workflow._prepare_activity = AsyncMock(  # type: ignore[method-assign]
        return_value=("execute_agent_task", "agent-general", {})
    )
    workflow._run_activity = AsyncMock(  # type: ignore[method-assign]
        return_value={"content": {"summary": "primary result"}}
    )

    result = await workflow._execute_node(_node(), {}, None, {})  # type: ignore[arg-type]

    assert result["content"]["summary"] == "primary result"
    assert result["fallback"] == {
        "used": False,
        "primaryAgent": "primary",
        "fallbackAgent": "standby",
        "reason": None,
    }


@pytest.mark.asyncio
async def test_agent_failure_executes_standby_and_preserves_reason() -> None:
    workflow = SwarmRunWorkflow()
    workflow._project = AsyncMock()  # type: ignore[method-assign]
    workflow._prepare_activity = AsyncMock(  # type: ignore[method-assign]
        return_value=("execute_agent_task", "agent-general", {})
    )
    workflow._run_activity = AsyncMock(  # type: ignore[method-assign]
        side_effect=[
            RuntimeError("primary unavailable"),
            {"content": {"summary": "standby result"}},
        ]
    )

    result = await workflow._execute_node(_node(), {}, None, {})  # type: ignore[arg-type]

    assert result["content"]["summary"] == "standby result"
    assert result["fallback"]["used"] is True
    assert result["fallback"]["fallbackAgent"] == "standby"
    assert result["fallback"]["reason"] == {
        "type": "RuntimeError",
        "message": "primary unavailable",
    }
    workflow._project.assert_any_await(
        "agent.fallback.selected",
        {
            "nodeKey": "diagnose",
            "taskInstanceKey": "diagnose:fallback",
            "primaryAgent": "primary",
            "fallbackAgent": "standby",
            "error": {"type": "RuntimeError", "message": "primary unavailable"},
        },
    )
