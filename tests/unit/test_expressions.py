import pytest
from swarmcore_spec import ExpressionError, evaluate_condition, render_templates


def test_conditions_and_templates_are_safe_and_typed() -> None:
    context = {
        "input": {"route": "publish"},
        "tasks": {"research": {"output": {"score": 4, "facts": ["a"]}}},
    }

    assert evaluate_condition('input.route == "publish"', context)
    assert evaluate_condition("tasks.research.output.score >= 3", context)
    assert render_templates("{{ tasks.research.output.facts }}", context) == ["a"]
    assert render_templates({"label": "route={{ input.route }}"}, context) == {
        "label": "route=publish"
    }


@pytest.mark.parametrize(
    "expression",
    ["__import__('os')", "input.value or true", "input.value == unknown"],
)
def test_unsafe_or_ambiguous_conditions_are_rejected(expression: str) -> None:
    with pytest.raises(ExpressionError):
        evaluate_condition(expression, {"input": {"value": True}})
