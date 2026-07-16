from __future__ import annotations

import json
import re
from typing import Any

_PATH = r"[a-zA-Z_][a-zA-Z0-9_-]*(?:\.[a-zA-Z_][a-zA-Z0-9_-]*)*"
_CONDITION = re.compile(
    rf"^\s*(?P<left>{_PATH})(?:\s*(?P<op>==|!=|<=|>=|<|>)\s*(?P<right>.+?))?\s*$"
)
_EXACT_TEMPLATE = re.compile(rf"^\s*\{{\{{\s*(?P<path>{_PATH})\s*\}}\}}\s*$")
_TEMPLATE = re.compile(rf"\{{\{{\s*(?P<path>{_PATH})\s*\}}\}}")


class ExpressionError(ValueError):
    pass


def validate_condition(expression: str) -> None:
    match = _CONDITION.fullmatch(expression)
    if match is None:
        raise ExpressionError("condition uses unsupported syntax")
    if match.group("op") is not None:
        _literal(match.group("right"))


def evaluate_condition(expression: str, context: dict[str, Any]) -> bool:
    validate_condition(expression)
    match = _CONDITION.fullmatch(expression)
    if match is None:  # pragma: no cover - validate_condition already proved this
        raise ExpressionError("condition uses unsupported syntax")
    left = resolve_path(match.group("left"), context)
    operator = match.group("op")
    if operator is None:
        return bool(left)
    right = _literal(match.group("right"))
    if operator == "==":
        return bool(left == right)
    if operator == "!=":
        return bool(left != right)
    if not isinstance(left, int | float | str) or isinstance(left, bool):
        raise ExpressionError("ordered comparison requires a number or string")
    if not isinstance(right, type(left)) and not (
        isinstance(left, int | float) and isinstance(right, int | float)
    ):
        raise ExpressionError("ordered comparison operands have incompatible types")
    if operator == "<":
        return bool(left < right)
    if operator == "<=":
        return bool(left <= right)
    if operator == ">":
        return bool(left > right)
    return bool(left >= right)


def render_templates(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, dict):
        return {key: render_templates(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [render_templates(item, context) for item in value]
    if not isinstance(value, str):
        return value
    exact = _EXACT_TEMPLATE.fullmatch(value)
    if exact is not None:
        return resolve_path(exact.group("path"), context)

    def replace(match: re.Match[str]) -> str:
        resolved = resolve_path(match.group("path"), context)
        if isinstance(resolved, str):
            return resolved
        return json.dumps(resolved, ensure_ascii=False, sort_keys=True)

    return _TEMPLATE.sub(replace, value)


def resolve_path(path: str, context: dict[str, Any]) -> Any:
    current: Any = context
    for segment in path.split("."):
        if not isinstance(current, dict) or segment not in current:
            raise ExpressionError(f"path {path!r} is not available")
        current = current[segment]
    return current


def _literal(value: str) -> Any:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ExpressionError("condition literal must be valid JSON") from exc
    if isinstance(parsed, dict | list):
        raise ExpressionError("condition literal must be a scalar")
    return parsed
