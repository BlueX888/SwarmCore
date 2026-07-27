from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID

from swarmcore_application.queries import is_retryable_run_failure, render_run_snapshot
from swarmcore_domain import uuid7


def _run(*, status: str = "FAILED") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid7(),
        status=status,
        input={},
        output=None,
        output_ref=None,
        next_event_seq=3,
        earliest_available_seq=1,
        plan_hash="plan",
        usage={},
        started_at=datetime(2026, 7, 24, tzinfo=UTC),
        completed_at=datetime(2026, 7, 24, 0, 1, tzinfo=UTC),
    )


def _task(*, status: str = "FAILED") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid7(),
        node_key="read-documents",
        node_type="tool",
        status=status,
        dependencies=[],
        retry_generation=0,
    )


def test_retry_task_requires_retryable_run_failure() -> None:
    run = _run()
    task = _task()
    snapshot = render_run_snapshot(run, [task], retryable=True)
    assert "retry_task" in snapshot["allowedActions"]
    assert snapshot["tasks"][0]["allowedActions"] == ["retry_task"]

    blocked = render_run_snapshot(run, [task], retryable=False)
    assert "retry_task" not in blocked["allowedActions"]
    assert blocked["tasks"][0]["allowedActions"] == []


def test_is_retryable_run_failure_reads_payload_flag() -> None:
    assert is_retryable_run_failure(None) is False
    assert (
        is_retryable_run_failure(SimpleNamespace(payload={"code": "GRAPH_DEADLOCK"})) is False
    )
    assert (
        is_retryable_run_failure(
            SimpleNamespace(payload={"code": "TASK_FAILED", "retryable": True})
        )
        is True
    )
    assert (
        is_retryable_run_failure(
            SimpleNamespace(payload={"code": "TASK_FAILED", "retryable": "true"})
        )
        is False
    )


def test_render_run_snapshot_preserves_task_error_payload() -> None:
    task_id = uuid7()
    task = _task()
    task.id = task_id
    error = {"type": "ActivityError", "message": "GatewayError: token references an unknown tool"}
    snapshot = render_run_snapshot(
        _run(),
        [task],
        errors={task_id: error},
        retryable=False,
    )
    assert snapshot["tasks"][0]["error"] == error
    assert isinstance(snapshot["runId"], str)
    assert UUID(snapshot["runId"])

    task.status = "SUCCEEDED"
    cleared = render_run_snapshot(
        _run(status="SUCCEEDED"),
        [task],
        errors={task_id: error},
        retryable=False,
    )
    assert cleared["tasks"][0]["error"] is None
