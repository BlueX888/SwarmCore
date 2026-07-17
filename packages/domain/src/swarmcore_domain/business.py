from enum import StrEnum


class WorkItemStatus(StrEnum):
    DRAFT = "DRAFT"
    READY = "READY"
    IN_REVIEW = "IN_REVIEW"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class BlobStatus(StrEnum):
    PENDING = "PENDING"
    SCANNING = "SCANNING"
    AVAILABLE = "AVAILABLE"
    REJECTED = "REJECTED"
    DELETED = "DELETED"


class EvaluationStatus(StrEnum):
    ACCEPTED = "ACCEPTED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FindingStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    WAIVED = "WAIVED"


_FINDING_TRANSITIONS: dict[FindingStatus, frozenset[FindingStatus]] = {
    FindingStatus.OPEN: frozenset(
        {FindingStatus.ACKNOWLEDGED, FindingStatus.RESOLVED, FindingStatus.WAIVED}
    ),
    FindingStatus.ACKNOWLEDGED: frozenset(
        {FindingStatus.RESOLVED, FindingStatus.WAIVED}
    ),
    FindingStatus.RESOLVED: frozenset({FindingStatus.OPEN}),
    FindingStatus.WAIVED: frozenset({FindingStatus.OPEN}),
}


def can_transition_finding(current: FindingStatus, target: FindingStatus) -> bool:
    return target in _FINDING_TRANSITIONS.get(current, frozenset())
