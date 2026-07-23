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
MANIFEST_V2 = _load("manifest-v2.json")
SCHEMAS = {
    "schema://contract/case@1": _load("case.schema.json"),
    "schema://contract/validation-input@1": _load("input.schema.json"),
    "schema://contract/validation-input@2": _load("input-v2.schema.json"),
    "schema://contract/validation-result@1": _load("output.schema.json"),
    "schema://contract/checklist-rule@1": _load("rule.schema.json"),
    "schema://contract/document-extraction@1": _load("extraction.schema.json"),
}
DEFAULT_RULES = _load("default-rules.json")
VIEW_DEFINITION = _load("view-definition.json")
STRATEGIES = {
    "strategy://contract-integrity/validate@1": _load("strategy.json"),
}
REFERENCES = frozenset(
    {
        *SCHEMAS,
        *STRATEGIES,
        "agent://contract/document-classifier@1",
        "agent://contract/field-extractor@1",
        "tool://document/read@1",
        "tool://rules/evaluate@1",
        "tool://contract/cross-file-consistency@1",
        "tool://workbench/record-evaluation@1",
        "tool://report/render@1",
        "report://contract/validation@1",
        "view://contract-integrity/work-item@1",
    }
)

__all__ = [
    "DEFAULT_RULES",
    "MANIFEST",
    "MANIFEST_V2",
    "REFERENCES",
    "SCHEMAS",
    "STRATEGIES",
    "VIEW_DEFINITION",
]
