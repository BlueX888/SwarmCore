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
    "schema://contract/post-evaluation-case@1": _load("case.schema.json"),
    "schema://contract/post-evaluation-input@2": _load("input.schema.json"),
    "schema://contract/post-evaluation-result@1": _load("output.schema.json"),
}
VIEW_DEFINITION = _load("view-definition.json")
STRATEGIES = {
    "strategy://contract-post-evaluation/generate@7": _load("strategy.json"),
}
REFERENCES = frozenset(
    {
        *SCHEMAS,
        *STRATEGIES,
        "agent://contract/post-evaluation-analyst@1",
        "tool://document/read-versions@1",
        "tool://contract/post-evaluation@1",
        "tool://report/render-post-evaluation@1",
        "tool://workbench/record-post-evaluation@1",
        "report://contract/post-evaluation@1",
        "view://contract-post-evaluation/case@1",
    }
)

__all__ = [
    "MANIFEST",
    "REFERENCES",
    "SCHEMAS",
    "STRATEGIES",
    "VIEW_DEFINITION",
]
