from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


def _load(name: str) -> dict[str, Any]:
    value = json.loads(files(__package__).joinpath(name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"capability asset must be an object: {name}")
    return value


MANIFEST = _load("manifest.json")
SCHEMAS = {
    "schema://contract/case@1": _load("case.schema.json"),
    "schema://contract/validation-input@1": _load("input.schema.json"),
    "schema://contract/validation-result@1": _load("output.schema.json"),
    "schema://contract/checklist-rule@1": _load("rule.schema.json"),
}
DEFAULT_RULES = _load("default-rules.json")
VIEW_DEFINITION = _load("view-definition.json")
REFERENCES = frozenset(
    {
        *SCHEMAS,
        "strategy://contract-integrity/validate@1",
        "tool://rules/evaluate@1",
        "tool://workbench/record-evaluation@1",
        "tool://report/render@1",
        "report://contract/validation@1",
        "view://contract-integrity/work-item@1",
    }
)

__all__ = ["DEFAULT_RULES", "MANIFEST", "REFERENCES", "SCHEMAS", "VIEW_DEFINITION"]
