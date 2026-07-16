from swarmcore_domain import RunStatus, can_transition_run


def test_terminal_run_states_are_irreversible() -> None:
    terminal = (
        RunStatus.REJECTED,
        RunStatus.CANCELLED,
        RunStatus.SUCCEEDED,
        RunStatus.FAILED,
        RunStatus.TIMED_OUT,
    )
    assert all(not can_transition_run(status, RunStatus.RUNNING) for status in terminal)


def test_design_run_transitions() -> None:
    assert can_transition_run(RunStatus.ACCEPTED, RunStatus.VALIDATING)
    assert can_transition_run(RunStatus.RUNNING, RunStatus.CANCELLING)
    assert can_transition_run(RunStatus.CANCELLING, RunStatus.COMPENSATING)
    assert not can_transition_run(RunStatus.ACCEPTED, RunStatus.SUCCEEDED)
