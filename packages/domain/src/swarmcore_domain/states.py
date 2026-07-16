from enum import StrEnum


class RunStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    VALIDATING = "VALIDATING"
    REJECTED = "REJECTED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_INPUT = "WAITING_INPUT"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    PAUSING = "PAUSING"
    PAUSED = "PAUSED"
    CANCELLING = "CANCELLING"
    COMPENSATING = "COMPENSATING"
    CANCELLED = "CANCELLED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    BLOCKED = "BLOCKED"
    READY = "READY"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    RETRYING = "RETRYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"


class AttemptStatus(StrEnum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    HEARTBEATING = "HEARTBEATING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"
    LOST = "LOST"


_RUN_TRANSITIONS: dict[RunStatus, frozenset[RunStatus]] = {
    RunStatus.ACCEPTED: frozenset({RunStatus.VALIDATING, RunStatus.CANCELLING, RunStatus.FAILED}),
    RunStatus.VALIDATING: frozenset({RunStatus.REJECTED, RunStatus.QUEUED, RunStatus.CANCELLING}),
    RunStatus.QUEUED: frozenset({RunStatus.RUNNING, RunStatus.PAUSING, RunStatus.CANCELLING}),
    RunStatus.RUNNING: frozenset(
        {
            RunStatus.WAITING_INPUT,
            RunStatus.WAITING_APPROVAL,
            RunStatus.PAUSING,
            RunStatus.CANCELLING,
            RunStatus.SUCCEEDED,
            RunStatus.FAILED,
            RunStatus.TIMED_OUT,
        }
    ),
    RunStatus.WAITING_INPUT: frozenset(
        {RunStatus.RUNNING, RunStatus.PAUSING, RunStatus.CANCELLING}
    ),
    RunStatus.WAITING_APPROVAL: frozenset(
        {RunStatus.RUNNING, RunStatus.PAUSING, RunStatus.CANCELLING}
    ),
    RunStatus.PAUSING: frozenset({RunStatus.PAUSED, RunStatus.RUNNING, RunStatus.CANCELLING}),
    RunStatus.PAUSED: frozenset({RunStatus.RUNNING, RunStatus.CANCELLING}),
    RunStatus.CANCELLING: frozenset({RunStatus.CANCELLED, RunStatus.COMPENSATING}),
    RunStatus.COMPENSATING: frozenset({RunStatus.CANCELLED, RunStatus.FAILED}),
}


def can_transition_run(current: RunStatus, target: RunStatus) -> bool:
    return target in _RUN_TRANSITIONS.get(current, frozenset())
