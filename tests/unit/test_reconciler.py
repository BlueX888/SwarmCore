from swarmcore_persistence import ProjectionReconciler


def test_reconciler_knows_all_phase_one_run_terminal_events() -> None:
    statuses = ProjectionReconciler.STATUS_BY_EVENT
    assert statuses["run.completed"] == "SUCCEEDED"
    assert statuses["run.cancelled"] == "CANCELLED"
    assert statuses["run.failed"] == "FAILED"
