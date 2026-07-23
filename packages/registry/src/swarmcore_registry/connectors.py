from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConnectorModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class ConnectorOperation(ConnectorModel):
    name: str = Field(min_length=1, max_length=128)
    access_mode: Literal["READ", "WRITE", "READ_WRITE"] = Field(alias="accessMode")
    risk: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    idempotent: bool


class ConnectorDefinition(ConnectorModel):
    ref: str
    display_name: str = Field(alias="displayName", min_length=1, max_length=128)
    resource_kinds: tuple[str, ...] = Field(alias="resourceKinds", min_length=1)
    operations: tuple[ConnectorOperation, ...] = Field(min_length=1)
    configuration_schema: dict[str, Any] = Field(alias="configurationSchema")

    @model_validator(mode="after")
    def validate_definition(self) -> ConnectorDefinition:
        if not self.ref.startswith("connector://") or "@" not in self.ref:
            raise ValueError("CONNECTOR_REFERENCE_INVALID")
        if len(self.resource_kinds) != len(set(self.resource_kinds)):
            raise ValueError("connector resource kinds must be unique")
        names = [operation.name for operation in self.operations]
        if len(names) != len(set(names)):
            raise ValueError("connector operations must be unique")
        return self


class ConnectorRegistry:
    def __init__(self, definitions: tuple[ConnectorDefinition, ...]) -> None:
        self._definitions = {definition.ref: definition for definition in definitions}
        if len(self._definitions) != len(definitions):
            raise ValueError("connector references must be unique")

    def resolve(self, reference: str) -> ConnectorDefinition:
        try:
            return self._definitions[reference]
        except KeyError as exc:
            raise LookupError(f"CONNECTOR_DEFINITION_NOT_FOUND: {reference}") from exc


FAKE_FILES_CONNECTOR = ConnectorDefinition(
    ref="connector://fake/files@1",
    displayName="Deterministic fake files",
    resourceKinds=("DOCUMENT_COLLECTION", "OBJECT_STORE", "OUTPUT_TARGET"),
    operations=(
        ConnectorOperation(name="health", accessMode="READ", risk="LOW", idempotent=True),
        ConnectorOperation(name="read", accessMode="READ", risk="LOW", idempotent=True),
        ConnectorOperation(name="write", accessMode="WRITE", risk="HIGH", idempotent=True),
    ),
    configurationSchema={"type": "object", "additionalProperties": True},
)


def builtin_connector_registry() -> ConnectorRegistry:
    return ConnectorRegistry((FAKE_FILES_CONNECTOR,))
