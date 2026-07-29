import pytest
from pydantic import ValidationError
from swarmcore_spec import DuplicateKeyError, parse_spec

VALID_SPEC = """
apiVersion: swarmcore.io/v1
kind: SwarmStrategy
metadata:
  name: research-review
spec:
  inputSchema:
    type: object
  outputSchema:
    type: object
  defaults:
    model: model://general
  agents:
    researcher:
      role: researcher
      instructions: Research the subject.
      tools: [tool://search]
    reviewer:
      role: reviewer
      instructions: Review the findings.
  graph:
    entrypoint: research
    nodes:
      research:
        type: agent
        agent: researcher
      review:
        type: agent
        agent: reviewer
        dependsOn: [research]
        input:
          result: "{{ tasks.research.output }}"
      final:
        type: reducer
        reducer: merge_object
        dependsOn: [research, review]
    output:
      report: "{{ tasks.final.output }}"
"""


def test_parse_valid_yaml() -> None:
    strategy = parse_spec(VALID_SPEC)
    assert strategy.api_version == "swarmcore.io/v1"
    assert strategy.spec.budget.max_parallelism == 8
    assert strategy.spec.graph.nodes.root["review"].depends_on == ["research"]


def test_parse_agent_fallback() -> None:
    strategy = parse_spec(
        VALID_SPEC.replace(
            "        agent: researcher",
            "        agent: researcher\n        fallbackAgent: reviewer",
            1,
        )
    )

    node = strategy.spec.graph.nodes.root["research"]
    assert node.type == "agent"
    assert node.fallback_agent == "reviewer"


def test_reject_duplicate_yaml_keys() -> None:
    with pytest.raises(DuplicateKeyError, match="duplicate key"):
        parse_spec(VALID_SPEC.replace("  name: research-review", "  name: first\n  name: second"))


def test_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        parse_spec(
            VALID_SPEC.replace(
                "  name: research-review", "  name: research-review\n  unknown: true"
            )
        )


def test_reject_oversized_document() -> None:
    with pytest.raises(ValueError, match="1 MiB"):
        parse_spec(" " * (1024 * 1024 + 1))
