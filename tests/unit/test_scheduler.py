from swarmcore_runtime_temporal.scheduler import NodeState, blocked_by_failure, ready_nodes

NODES = [
    {"key": "a", "dependencies": []},
    {"key": "b", "dependencies": []},
    {"key": "c", "dependencies": ["a", "b"]},
]


def test_ready_nodes_are_stable_and_bounded() -> None:
    states = {key: NodeState.PENDING for key in ("a", "b", "c")}
    assert ready_nodes(NODES, states, max_parallelism=1) == ("a",)
    assert ready_nodes(NODES, states, max_parallelism=2) == ("a", "b")


def test_join_waits_for_all_dependencies() -> None:
    states = {"a": NodeState.SUCCEEDED, "b": NodeState.RUNNING, "c": NodeState.PENDING}
    assert ready_nodes(NODES, states, max_parallelism=8) == ()
    states["b"] = NodeState.SUCCEEDED
    assert ready_nodes(NODES, states, max_parallelism=8) == ("c",)


def test_failed_dependency_blocks_downstream() -> None:
    states = {"a": NodeState.FAILED, "b": NodeState.SUCCEEDED, "c": NodeState.PENDING}
    assert blocked_by_failure(NODES, states) == ("c",)


def test_blocked_dependency_propagates_to_downstream() -> None:
    states = {"a": NodeState.FAILED, "b": NodeState.SUCCEEDED, "c": NodeState.PENDING}
    states["c"] = NodeState.BLOCKED
    nodes = [*NODES, {"key": "d", "dependencies": ["c"]}]
    states["d"] = NodeState.PENDING

    assert ready_nodes(nodes, states, max_parallelism=8) == ()
    assert blocked_by_failure(nodes, states) == ("d",)
