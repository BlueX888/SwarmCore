from swarmcore_runtime_temporal import SwarmRunWorkflow


def test_initial_run_lifecycle_events_include_execution_metadata_without_input() -> None:
    payloads = SwarmRunWorkflow._initial_run_event_payloads(
        {
            "planHash": "a" * 64,
            "strategyVersionId": "strategy-version",
            "policyRevision": "policy-7",
            "input": {"secret": "must-not-be-copied"},
        },
        {
            "plan_version": "execution-plan.v1",
            "runtime_version": "temporal-runtime.v1",
            "registry_snapshot": "registry-4",
            "policy_revision": "stale-policy",
            "entrypoint": "fanout",
            "nodes": [{"key": "fanout"}, {"key": "reduce"}],
            "budget": {"maxParallelism": 4},
        },
    )

    assert payloads == {
        "run.validating": {
            "planHash": "a" * 64,
            "strategyVersionId": "strategy-version",
            "planVersion": "execution-plan.v1",
            "policyRevision": "policy-7",
            "registrySnapshot": "registry-4",
        },
        "run.queued": {
            "taskQueue": "swarm-control",
            "nodeCount": 2,
            "maxParallelism": 4,
            "entrypoint": "fanout",
        },
        "run.started": {
            "nodeCount": 2,
            "maxParallelism": 4,
            "runtimeVersion": "temporal-runtime.v1",
        },
    }
    assert "must-not-be-copied" not in repr(payloads)
