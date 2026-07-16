from pathlib import Path

import pytest
from sqlalchemy import UniqueConstraint
from swarmcore_domain import RunStatus, can_transition_run
from swarmcore_persistence.models import ApprovalRequest, ExternalInputRequest, Run
from swarmcore_runtime_temporal import SwarmRunWorkflow


def test_human_request_tables_are_scoped_and_one_shot() -> None:
    for model in (ApprovalRequest, ExternalInputRequest):
        columns = set(model.__table__.columns.keys())
        assert {"tenant_id", "project_id", "run_id", "status", "handler_command_id"} <= columns
        assert model.__table__.c.handler_command_id.unique

    run_constraints = {
        tuple(constraint.columns.keys())
        for constraint in Run.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("tenant_id", "project_id", "id") in run_constraints


def test_terminal_state_machine_remains_closed() -> None:
    assert not can_transition_run(RunStatus.FAILED, RunStatus.RUNNING)
    assert not can_transition_run(RunStatus.SUCCEEDED, RunStatus.RUNNING)


def test_phase2a_migration_enables_rls_without_rewriting_phase_one() -> None:
    migration = Path(
        "packages/persistence/alembic/versions/0002_phase2a_human_control.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0001_phase1_core"' in migration
    assert "approval_requests" in migration
    assert "external_input_requests" in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration


@pytest.mark.asyncio
async def test_workflow_commands_are_ordered_and_request_idempotent() -> None:
    workflow = SwarmRunWorkflow()
    workflow._last_applied_command_seq = 1
    out_of_order = await workflow.apply_command(
        {"commandSeq": 3, "requestId": "late", "type": "cancel"}
    )
    assert out_of_order == {
        "status": "REJECTED",
        "code": "COMMAND_OUT_OF_ORDER",
        "lastAppliedCommandSeq": 1,
    }
    first = await workflow.apply_command(
        {"commandSeq": 2, "requestId": "cancel-once", "type": "cancel"}
    )
    duplicate = await workflow.apply_command(
        {"commandSeq": 99, "requestId": "cancel-once", "type": "cancel"}
    )
    assert first == {"status": "APPLIED"}
    assert duplicate == first
    assert workflow._last_applied_command_seq == 2
