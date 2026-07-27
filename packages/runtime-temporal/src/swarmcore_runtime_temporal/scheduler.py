from __future__ import annotations

from enum import StrEnum
from typing import Any


class NodeState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"


def ready_nodes(
    nodes: list[dict[str, Any]],
    states: dict[str, NodeState],
    *,
    max_parallelism: int,
) -> tuple[str, ...]:
    """Return a stable, bounded batch whose dependency nodes all succeeded."""
    ready = [
        str(node["key"])
        for node in nodes
        if states[str(node["key"])] == NodeState.PENDING
        and all(
            states[key] in {NodeState.SUCCEEDED, NodeState.SKIPPED}
            for key in node.get("dependencies", [])
        )
    ]
    return tuple(sorted(ready)[:max_parallelism])


def blocked_by_failure(
    nodes: list[dict[str, Any]], states: dict[str, NodeState]
) -> tuple[str, ...]:
    terminal_failure = {NodeState.FAILED, NodeState.CANCELLED, NodeState.BLOCKED}
    blocked = [
        str(node["key"])
        for node in nodes
        if states[str(node["key"])] == NodeState.PENDING
        and any(states[key] in terminal_failure for key in node.get("dependencies", []))
    ]
    return tuple(sorted(blocked))


def propagate_failure_blocks(
    nodes: list[dict[str, Any]], states: dict[str, NodeState], *, blocked_state: NodeState
) -> tuple[str, ...]:
    """Mark all transitive failure dependents until a fixed point; return newly blocked keys."""
    newly: list[str] = []
    while True:
        batch = blocked_by_failure(nodes, states)
        if not batch:
            break
        for key in batch:
            states[key] = blocked_state
            newly.append(key)
    return tuple(newly)
