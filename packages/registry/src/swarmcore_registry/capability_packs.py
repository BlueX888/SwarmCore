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
    r"^(agent|connector|model|tool|strategy|schema|report|view)://[^\s@]+@[^\s@]+$"
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


class CapabilitySubjectRole(PackModel):
    key: str = Field(min_length=1, max_length=128)
    object_type: str = Field(alias="objectType", min_length=1, max_length=128)
    role: str
    min: int = Field(default=0, ge=0)
    max: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def valid_range(self) -> CapabilitySubjectRole:
        if self.role not in {"PRIMARY", "COMPARISON", "EVIDENCE", "RELATED"}:
            raise ValueError("unsupported subject role")
        if self.max is not None and self.max < self.min:
            raise ValueError("subject role max must be greater than or equal to min")
        return self


class CapabilityCase(PackModel):
    type: str = Field(min_length=1, max_length=128)
    schema_ref: str = Field(alias="schema")
    subjects_required: bool = Field(default=True, alias="subjectsRequired")
    subject_roles: tuple[CapabilitySubjectRole, ...] = Field(default=(), alias="subjectRoles")


class CapabilityDecisionSlot(PackModel):
    slot: str = Field(min_length=1, max_length=128)
    required: bool = True
    input_schema: str = Field(alias="inputSchema")
    output_schema: str = Field(alias="outputSchema")
    allowed_types: tuple[str, ...] = Field(alias="allowedTypes", min_length=1)


class CapabilityResourceSlot(PackModel):
    slot: str = Field(min_length=1, max_length=128)
    required: bool = True
    resource_kinds: tuple[str, ...] = Field(alias="resourceKinds", min_length=1)
    access_mode: str = Field(alias="accessMode")


class CapabilityDocumentRequirement(PackModel):
    category: str = Field(min_length=1, max_length=128)
    required: bool = True


class CapabilityPackSpec(PackModel):
    work_item_type: str | None = Field(
        default=None, alias="workItemType", min_length=1, max_length=128
    )
    work_item_schema: str | None = Field(default=None, alias="workItemSchema")
    case: CapabilityCase | None = None
    input_schema: str = Field(alias="inputSchema")
    output_schema: str = Field(alias="outputSchema")
    strategies: CapabilityPackStrategies
    agents: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    rules: CapabilityPackRules | None = None
    decisions: tuple[CapabilityDecisionSlot, ...] = ()
    resources: tuple[CapabilityResourceSlot, ...] = ()
    documents: tuple[CapabilityDocumentRequirement, ...] = ()
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
        decision_slots = [item.slot for item in self.decisions]
        resource_slots = [item.slot for item in self.resources]
        if len(decision_slots) != len(set(decision_slots)):
            raise ValueError("decision slot keys must be unique")
        if len(resource_slots) != len(set(resource_slots)):
            raise ValueError("resource slot keys must be unique")
        document_categories = [item.category for item in self.documents]
        if len(document_categories) != len(set(document_categories)):
            raise ValueError("document requirement categories must be unique")
        return self

    def references(self) -> tuple[str, ...]:
        refs = [
            self.input_schema,
            self.output_schema,
            self.strategies.execute,
            *self.agents,
            *self.tools,
            self.report.template,
            self.ui.view_definition,
        ]
        if self.work_item_schema is not None:
            refs.append(self.work_item_schema)
        if self.case is not None:
            refs.append(self.case.schema_ref)
        for decision in self.decisions:
            refs.extend((decision.input_schema, decision.output_schema))
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
        if (
            self.api_version not in {"swarmcore.io/v1", "swarmcore.io/v2"}
            or self.kind != "CapabilityPack"
        ):
            raise ValueError("unsupported capability pack envelope")
        if self.api_version == "swarmcore.io/v1":
            if self.spec.work_item_type is None or self.spec.work_item_schema is None:
                raise ValueError("v1 capability packs require workItemType and workItemSchema")
            if (
                self.spec.case is not None
                or self.spec.decisions
                or self.spec.resources
                or self.spec.documents
            ):
                raise ValueError("v1 capability packs cannot declare v2 slots")
        elif self.spec.case is None:
            raise ValueError("v2 capability packs require case")
        expected = f"capability.{self.metadata.name}"
        if self.spec.events.namespace != expected:
            raise ValueError(f"event namespace must be {expected}")
        return self

    @property
    def case_type(self) -> str:
        if self.spec.case is not None:
            return self.spec.case.type
        assert self.spec.work_item_type is not None
        return self.spec.work_item_type


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
    if parsed.api_version == "swarmcore.io/v1":
        # v2 added optional fields with empty defaults. They are not part of the
        # v1 wire contract and must not change hashes of published v1 versions.
        for field in ("case", "decisions", "resources", "documents"):
            normalized["spec"].pop(field, None)
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
