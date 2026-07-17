from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_PACK_NAME = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_VERSIONED_REF = re.compile(
    r"^(agent|model|tool|strategy|schema|report|view)://[^\s@]+@[^\s@]+$"
)
_FORBIDDEN_KEYS = {"module", "classPath", "script", "componentUrl"}


class PackModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class CapabilityPackMetadata(PackModel):
    name: str
    version: str

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        if not _PACK_NAME.fullmatch(value):
            raise ValueError("pack name must be lowercase kebab-case")
        return value

    @field_validator("version")
    @classmethod
    def valid_version(cls, value: str) -> str:
        if not _SEMVER.fullmatch(value):
            raise ValueError("pack version must be semantic major.minor.patch")
        return value


class CapabilityPackStrategies(PackModel):
    execute: str


class CapabilityPackRules(PackModel):
    schema_ref: str = Field(alias="schema")


class CapabilityPackReport(PackModel):
    template: str


class CapabilityPackEvents(PackModel):
    namespace: str


class CapabilityPackUi(PackModel):
    view_definition: str = Field(alias="viewDefinition")


class CapabilityPackSpec(PackModel):
    work_item_type: str = Field(alias="workItemType", min_length=1, max_length=128)
    work_item_schema: str = Field(alias="workItemSchema")
    input_schema: str = Field(alias="inputSchema")
    output_schema: str = Field(alias="outputSchema")
    strategies: CapabilityPackStrategies
    agents: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    rules: CapabilityPackRules | None = None
    report: CapabilityPackReport
    permissions: tuple[str, ...]
    events: CapabilityPackEvents
    ui: CapabilityPackUi

    @model_validator(mode="after")
    def references_are_versioned(self) -> CapabilityPackSpec:
        refs = list(self.references())
        invalid = [value for value in refs if not _VERSIONED_REF.fullmatch(value)]
        if invalid:
            raise ValueError(f"all resource references must be immutable: {', '.join(invalid)}")
        if len(self.agents) != len(set(self.agents)) or len(self.tools) != len(set(self.tools)):
            raise ValueError("agent and tool references must be unique")
        if len(self.permissions) != len(set(self.permissions)):
            raise ValueError("permissions must be unique")
        return self

    def references(self) -> tuple[str, ...]:
        refs = [
            self.work_item_schema,
            self.input_schema,
            self.output_schema,
            self.strategies.execute,
            *self.agents,
            *self.tools,
            self.report.template,
            self.ui.view_definition,
        ]
        if self.rules is not None:
            refs.append(self.rules.schema_ref)
        return tuple(refs)


class CapabilityPackManifest(PackModel):
    api_version: str = Field(alias="apiVersion")
    kind: str
    metadata: CapabilityPackMetadata
    spec: CapabilityPackSpec

    @model_validator(mode="after")
    def validate_envelope(self) -> CapabilityPackManifest:
        if self.api_version != "swarmcore.io/v1" or self.kind != "CapabilityPack":
            raise ValueError("unsupported capability pack envelope")
        expected = f"capability.{self.metadata.name}"
        if self.spec.events.namespace != expected:
            raise ValueError(f"event namespace must be {expected}")
        return self


class CapabilityReferenceCatalog(PackModel):
    references: frozenset[str]

    @classmethod
    def from_iterable(cls, values: Iterable[str]) -> CapabilityReferenceCatalog:
        return cls(references=frozenset(values))

    def resolve(self, reference: str) -> str:
        if reference in self.references:
            return reference
        raise ValueError(f"CAPABILITY_REFERENCE_MISSING: {reference}")


def normalize_manifest(manifest: CapabilityPackManifest | Mapping[str, Any]) -> dict[str, Any]:
    parsed = (
        manifest
        if isinstance(manifest, CapabilityPackManifest)
        else CapabilityPackManifest.model_validate(manifest)
    )
    normalized = parsed.model_dump(mode="json", by_alias=True, exclude_none=True)
    _reject_code_entrypoints(normalized)
    return normalized


def hash_manifest(manifest: CapabilityPackManifest | Mapping[str, Any]) -> str:
    encoded = json.dumps(
        normalize_manifest(manifest), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def resolve_manifest(
    manifest: CapabilityPackManifest | Mapping[str, Any],
    catalog: CapabilityReferenceCatalog,
) -> tuple[CapabilityPackManifest, dict[str, str]]:
    parsed = (
        manifest
        if isinstance(manifest, CapabilityPackManifest)
        else CapabilityPackManifest.model_validate(manifest)
    )
    normalize_manifest(parsed)
    resolved = {reference: catalog.resolve(reference) for reference in parsed.spec.references()}
    return parsed, resolved


def load_trusted_manifests(
    directory: Path, catalog: CapabilityReferenceCatalog
) -> tuple[tuple[CapabilityPackManifest, dict[str, str]], ...]:
    loaded: list[tuple[CapabilityPackManifest, dict[str, str]]] = []
    for path in sorted(directory.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"manifest must be an object: {path}")
        loaded.append(resolve_manifest(payload, catalog))
    return tuple(loaded)


def _reject_code_entrypoints(value: Any) -> None:
    if isinstance(value, dict):
        forbidden = _FORBIDDEN_KEYS.intersection(value)
        if forbidden:
            name = sorted(forbidden)[0]
            raise ValueError(f"capability manifest contains code entrypoint: {name}")
        for nested in value.values():
            _reject_code_entrypoints(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_code_entrypoints(nested)
