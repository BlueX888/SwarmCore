from __future__ import annotations

import json
from copy import deepcopy
from importlib.resources import files
from typing import Any


def _load(name: str) -> dict[str, Any]:
    value = json.loads(files(__package__).joinpath(name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"capability asset must be an object: {name}")
    return value


MANIFEST = _load("manifest.json")
_ACCEPTED_MEDIA_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/json",
    "text/csv",
    "text/plain",
]
for _requirement in MANIFEST["spec"]["documents"]["requirements"]:
    _requirement.setdefault("acceptedMediaTypes", list(_ACCEPTED_MEDIA_TYPES))

SCHEMAS = {
    "schema://procurement-supplier-risk/case@1": _load("case.schema.json"),
    "schema://procurement-supplier-risk/input@1": _load("input.schema.json"),
    "schema://procurement-supplier-risk/input@2": _load("input.v2.schema.json"),
    "schema://procurement-supplier-risk/result@1": _load("output.schema.json"),
    "schema://procurement-supplier-risk/result@2": _load("output.v2.schema.json"),
}
STRATEGIES = {
    "strategy://procurement-supplier-risk/assess@5": _load("strategy.json"),
    "strategy://procurement-supplier-risk/assess@6": _load("strategy.v6.json"),
}
VIEW_DEFINITION = _load("view-definition.json")
REFERENCES = frozenset(
    {
        *SCHEMAS,
        *STRATEGIES,
        *MANIFEST["spec"]["agents"],
        *MANIFEST["spec"]["tools"],
        MANIFEST["spec"]["report"]["template"],
        MANIFEST["spec"]["ui"]["viewDefinition"],
        # Keep @5 pack refs resolvable for historical runs / dual registration.
        "agent://procurement/clause-evidence-analyst@3",
        "agent://supplier/risk-analyst@1",
        "agent://procurement/evidence-quality-reviewer@1",
        "tool://procurement/consistency-compare@1",
        "tool://supplier/risk-collect@1",
        "tool://supplier/risk-decide@1",
        "tool://procurement-supplier-risk/finalize@1",
        "strategy://procurement-supplier-risk/assess@5",
        "schema://procurement-supplier-risk/input@1",
        "schema://procurement-supplier-risk/result@1",
    }
)

# Preserve prior manifest snapshot for regression comparisons.
MANIFEST_V1_0_4 = deepcopy(MANIFEST)
MANIFEST_V1_0_4["metadata"]["version"] = "1.0.4"
MANIFEST_V1_0_4["spec"]["inputSchema"] = "schema://procurement-supplier-risk/input@1"
MANIFEST_V1_0_4["spec"]["outputSchema"] = "schema://procurement-supplier-risk/result@1"
MANIFEST_V1_0_4["spec"]["strategies"]["execute"] = (
    "strategy://procurement-supplier-risk/assess@5"
)
MANIFEST_V1_0_4["spec"]["agents"] = [
    "agent://procurement/clause-evidence-analyst@3",
    "agent://supplier/risk-analyst@1",
    "agent://procurement/evidence-quality-reviewer@1",
]
MANIFEST_V1_0_4["spec"]["tools"] = [
    "tool://document/read-versions@1",
    "tool://document/coverage-check@1",
    "tool://evidence/search@1",
    "tool://procurement/consistency-compare@1",
    "tool://supplier/risk-collect@1",
    "tool://supplier/performance-calculate@1",
    "tool://supplier/risk-decide@1",
    "tool://supplier/history-diff@1",
    "tool://procurement-supplier-risk/finalize@1",
    "tool://report/render-procurement-supplier-risk@1",
    "tool://workbench/record-procurement-supplier-risk@1",
]

__all__ = [
    "MANIFEST",
    "MANIFEST_V1_0_4",
    "REFERENCES",
    "SCHEMAS",
    "STRATEGIES",
    "VIEW_DEFINITION",
]
