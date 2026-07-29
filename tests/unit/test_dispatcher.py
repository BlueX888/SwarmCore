from datetime import timedelta
from typing import Any, cast

from swarmcore_command_dispatcher import CommandDispatcher, retry_delay


def test_dispatcher_retry_is_exponential_and_capped() -> None:
    assert retry_delay(1) == timedelta(seconds=2)
    assert retry_delay(5) == timedelta(seconds=32)
    assert retry_delay(100) == timedelta(minutes=5)


def test_dispatcher_accepts_an_isolated_temporal_task_queue() -> None:
    dispatcher = CommandDispatcher(
        cast(Any, object()),
        cast(Any, object()),
        worker_id="test",
        task_queue="swarm-control-document-verification",
        agent_task_queue="agent-document-verification",
        tool_task_queue="tool-document-verification",
    )
    assert dispatcher._task_queue == "swarm-control-document-verification"
    assert dispatcher._agent_task_queue == "agent-document-verification"
    assert dispatcher._tool_task_queue == "tool-document-verification"
