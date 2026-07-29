from __future__ import annotations

from jsonschema import Draft202012Validator
from swarmcore_application import StrategyService
from swarmcore_capability_swarm_calibration import MANIFEST, REFERENCES, SCHEMAS, STRATEGIES
from swarmcore_registry import (
    CapabilityPackManifest,
    CapabilityReferenceCatalog,
    builtin_registry,
    resolve_manifest,
)
from swarmcore_spec import SwarmStrategy


def test_swarm_calibration_assets_compile_and_close_all_dependencies() -> None:
    manifest = CapabilityPackManifest.model_validate(MANIFEST)
    strategy = SwarmStrategy.model_validate(
        STRATEGIES["strategy://swarm-calibration/assess@4"]
    )
    registry = builtin_registry()

    assert manifest.metadata.name == "swarm-calibration"
    assert manifest.metadata.version == "1.0.4"
    assert strategy.spec.budget.max_cost_usd == 1
    assert strategy.spec.budget.max_agents == 4
    assert set(manifest.spec.agents) <= REFERENCES
    assert set(manifest.spec.tools) <= REFERENCES
    assert all(registry.resolve_agent(ref) is not None for ref in manifest.spec.agents)
    assert all(registry.resolve_tool(ref) is not None for ref in manifest.spec.tools)
    for schema in SCHEMAS.values():
        Draft202012Validator.check_schema(schema)
    Draft202012Validator(SCHEMAS["schema://swarm-calibration/input@1"]).validate(
        {
            "workItemId": "00000000-0000-0000-0000-000000000001",
            "workItemRevisionId": "00000000-0000-0000-0000-000000000002",
            "evaluationId": "00000000-0000-0000-0000-000000000003",
            "payload": {
                "title": "Real issue calibration",
                "issueUrl": "https://github.com/temporalio/sdk-python/issues/782",
                "objective": "Verify the merged fix.",
                "acceptanceCriteria": ["Cite the merged pull request."],
                "sandbox": {
                    "enabled": True,
                    "testCommand": ["python", "-m", "compileall", "temporalio"],
                },
            },
            "attachmentManifestHash": "0" * 64,
            "configuration": {},
        }
    )

    resolved, snapshot = resolve_manifest(
        MANIFEST, CapabilityReferenceCatalog.from_iterable(REFERENCES)
    )
    assert set(snapshot) == set(resolved.spec.references())
    _, plan = StrategyService().compile(
        STRATEGIES[resolved.spec.strategies.execute],
        registry_snapshot=registry.snapshot_id,
        policy_revision="test",
    )
    assert set(plan.resolved_tools) == set(manifest.spec.tools)
    diagnosis = next(node for node in plan.nodes if node.key == "primary-diagnosis")
    assert diagnosis.config["fallbackAgent"] == "standby"
    revision = next(node for node in plan.nodes if node.key == "revision-diagnosis")
    assert revision.config["fallbackAgent"] == "standby"
    revision_score = next(node for node in plan.nodes if node.key == "revision-quality-score")
    assert revision_score.config["input"]["attempt"] == 2
    assert {node.key for node in plan.nodes} >= {
        "revision-loop",
        "selected-attempt",
        "normalize-attempt",
        "manual-review",
        "workflow-result",
    }
    assert sorted(plan.result_reducer)[-1] == "workflow-result"
    assert plan.budget["maxDuration"] == "PT12M"
