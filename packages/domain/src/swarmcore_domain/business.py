from enum import StrEnum


class BusinessObjectLifecycle(StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class SubjectRole(StrEnum):
    PRIMARY = "PRIMARY"
    COMPARISON = "COMPARISON"
    EVIDENCE = "EVIDENCE"
    RELATED = "RELATED"


class DecisionAssetType(StrEnum):
    CHECKLIST = "CHECKLIST"
    DECISION_TABLE = "DECISION_TABLE"
    EXPRESSION = "EXPRESSION"
    THRESHOLD = "THRESHOLD"


class ResourceKind(StrEnum):
    DOCUMENT_COLLECTION = "DOCUMENT_COLLECTION"
    API = "API"
    DATABASE_TABLE = "DATABASE_TABLE"
    KNOWLEDGE_BASE = "KNOWLEDGE_BASE"
    EVENT_STREAM = "EVENT_STREAM"
    OBJECT_STORE = "OBJECT_STORE"
    OUTPUT_TARGET = "OUTPUT_TARGET"


class ResourceAccessMode(StrEnum):
    READ = "READ"
    WRITE = "WRITE"
    SUBSCRIBE = "SUBSCRIBE"


class ResourceReplayability(StrEnum):
    REPLAYABLE = "REPLAYABLE"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    NON_REPLAYABLE = "NON_REPLAYABLE"


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
    FindingStatus.ACKNOWLEDGED: frozenset({FindingStatus.RESOLVED, FindingStatus.WAIVED}),
    FindingStatus.RESOLVED: frozenset({FindingStatus.OPEN}),
    FindingStatus.WAIVED: frozenset({FindingStatus.OPEN}),
}


def can_transition_finding(current: FindingStatus, target: FindingStatus) -> bool:
    return target in _FINDING_TRANSITIONS.get(current, frozenset())
