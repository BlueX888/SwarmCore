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
    terminal_failure = {NodeState.FAILED, NodeState.CANCELLED}
    blocked = [
        str(node["key"])
        for node in nodes
        if states[str(node["key"])] == NodeState.PENDING
        and any(states[key] in terminal_failure for key in node.get("dependencies", []))
    ]
    return tuple(sorted(blocked))
