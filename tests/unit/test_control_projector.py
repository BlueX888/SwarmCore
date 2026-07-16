from swarmcore_worker_control.adapters import PostgresTransitionProjector


def test_projector_maps_task_terminal_states() -> None:
    assert PostgresTransitionProjector._TASK_STATUS["task.completed"] == "SUCCEEDED"
    assert PostgresTransitionProjector._TASK_STATUS["task.failed"] == "FAILED"
