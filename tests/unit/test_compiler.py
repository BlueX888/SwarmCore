import pytest
from swarmcore_compiler import CompileError, Compiler, dag, parallel, sequential, supervisor
from swarmcore_spec import parse_spec

from .test_spec import VALID_SPEC


def test_compile_is_deterministic() -> None:
    strategy = parse_spec(VALID_SPEC)
    compiler = Compiler()

    first = compiler.compile(strategy, registry_snapshot="registry:1", policy_revision="policy:1")
    second = compiler.compile(strategy, registry_snapshot="registry:1", policy_revision="policy:1")

    assert first.plan_hash == second.plan_hash
    assert first.canonical_json() == second.canonical_json()
    assert [node.key for node in first.nodes] == ["research", "review", "final"]
    assert first.resolved_resources == ("model://general", "tool://search")


def test_reject_cycle() -> None:
    strategy = parse_spec(
        VALID_SPEC.replace("agent: researcher", "agent: researcher\n        dependsOn: [review]", 1)
    )
    with pytest.raises(CompileError, match="CYCLIC_DEPENDENCY"):
        Compiler().compile(strategy, registry_snapshot="r1", policy_revision="p1")


def test_reject_unknown_agent() -> None:
    strategy = parse_spec(VALID_SPEC.replace("agent: researcher", "agent: missing", 1))
    with pytest.raises(CompileError, match="UNKNOWN_AGENT"):
        Compiler().compile(strategy, registry_snapshot="r1", policy_revision="p1")


def test_reject_invalid_json_schema() -> None:
    strategy = parse_spec(VALID_SPEC.replace("type: object", "type: definitely-not-a-type", 1))
    with pytest.raises(CompileError, match="INVALID_JSON_SCHEMA"):
        Compiler().compile(strategy, registry_snapshot="r1", policy_revision="p1")


def test_resolve_agent_output_schema_into_plan() -> None:
    strategy = parse_spec(
        VALID_SPEC.replace(
            "      tools: [tool://search]",
            '      tools: [tool://search]\n      outputSchemaRef: "#/$defs/facts"',
        ).replace(
            "  graph:",
            "  $defs:\n    facts:\n      type: object\n      required: [facts]\n  graph:",
        )
    )
    plan = Compiler().compile(strategy, registry_snapshot="r1", policy_revision="p1")
    assert plan.resolved_agents["researcher"]["outputSchema"]["required"] == ["facts"]


AGENT = {"role": "worker", "instructions": "Do the assigned work."}


@pytest.mark.parametrize(
    "strategy",
    [
        sequential("sequential", {"one": AGENT, "two": AGENT}),
        parallel("parallel", {"one": AGENT, "two": AGENT}),
        dag("dag", {"one": AGENT, "two": AGENT}, {"two": ["one"]}),
        supervisor("supervisor", AGENT, {"one": AGENT, "two": AGENT}),
    ],
)
def test_phase_one_templates_compile(strategy: object) -> None:
    plan = Compiler().compile(strategy, registry_snapshot="r1", policy_revision="p1")  # type: ignore[arg-type]
    assert plan.nodes


def test_phase_one_rejects_schema_only_node_types_before_runtime() -> None:
    strategy = parse_spec(
        VALID_SPEC.replace(
            "type: reducer\n        reducer: merge_object",
            "type: emit\n        event: unsupported",
        )
    )
    with pytest.raises(CompileError, match="UNSUPPORTED_NODE_TYPE"):
        Compiler().compile(strategy, registry_snapshot="r1", policy_revision="p1")
