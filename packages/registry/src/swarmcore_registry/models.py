from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class ToolRisk(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AgentRegistration(FrozenModel):
    ref: str
    version: str
    role: str
    instructions: str
    model: str
    tools: tuple[str, ...] = ()
    output_schema: dict[str, Any] | None = Field(default=None, alias="outputSchema")


class ModelRegistration(FrozenModel):
    ref: str
    version: str
    runtime: str
    provider_model: str = Field(alias="providerModel")
    environments: tuple[str, ...]


class ToolRegistration(FrozenModel):
    ref: str
    version: str
    operation: str
    description: str
    risk: ToolRisk
    input_schema: dict[str, Any] = Field(alias="inputSchema")
    output_schema: dict[str, Any] = Field(alias="outputSchema")
    idempotent: bool
    side_effecting: bool = Field(alias="sideEffecting")
    cost_usd: float = Field(default=0.0, alias="costUsd", ge=0)
    recovery_policy: Literal["idempotent", "compensate", "manual"] = Field(
        alias="recoveryPolicy"
    )
    compensation_operation: str | None = Field(default=None, alias="compensationOperation")

    @model_validator(mode="after")
    def side_effects_require_idempotency(self) -> ToolRegistration:
        if self.side_effecting and self.recovery_policy == "idempotent" and not self.idempotent:
            raise ValueError("idempotent recovery requires the gateway effect id")
        if (self.recovery_policy == "compensate") != (self.compensation_operation is not None):
            raise ValueError("compensate recovery requires exactly one compensation operation")
        return self


class RegistrySnapshot(FrozenModel):
    snapshot_id: str = Field(alias="snapshotId")
    agents: tuple[AgentRegistration, ...] = ()
    models: tuple[ModelRegistration, ...] = ()
    tools: tuple[ToolRegistration, ...] = ()

    def resolve_agent(self, reference: str) -> AgentRegistration | None:
        return self._resolve(reference, self.agents)

    def resolve_model(self, reference: str) -> ModelRegistration | None:
        return self._resolve(reference, self.models)

    def resolve_tool(self, reference: str) -> ToolRegistration | None:
        return self._resolve(reference, self.tools)

    @staticmethod
    def _resolve(reference: str, values: tuple[Any, ...]) -> Any | None:
        exact = next((item for item in values if item.ref == reference), None)
        if exact is not None:
            return exact
        if "@" in reference:
            return None
        candidates = [item for item in values if item.ref.rsplit("@", 1)[0] == reference]
        return candidates[0] if len(candidates) == 1 else None

    @classmethod
    def create(
        cls,
        *,
        agents: tuple[AgentRegistration, ...] = (),
        models: tuple[ModelRegistration, ...] = (),
        tools: tuple[ToolRegistration, ...] = (),
    ) -> RegistrySnapshot:
        payload = {
            "agents": [item.model_dump(mode="json", by_alias=True) for item in agents],
            "models": [item.model_dump(mode="json", by_alias=True) for item in models],
            "tools": [item.model_dump(mode="json", by_alias=True) for item in tools],
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(encoded.encode()).hexdigest()[:16]
        return cls(
            snapshotId=f"registry:{digest}", agents=agents, models=models, tools=tools
        )


def builtin_registry() -> RegistrySnapshot:
    return RegistrySnapshot.create(
        agents=(
            AgentRegistration(
                ref="agent://builtin/researcher@1",
                version="1",
                role="researcher",
                instructions="Research the assigned topic and return structured findings.",
                model="model://general@1",
                tools=("tool://search@1",),
            ),
        ),
        models=(
            ModelRegistration(
                ref="model://general@1",
                version="1",
                runtime="agno",
                providerModel="openai:gpt-4o-mini",
                environments=("development", "production"),
            ),
            ModelRegistration(
                ref="model://fake-deterministic@1",
                version="1",
                runtime="fake-deterministic",
                providerModel="fake:deterministic",
                environments=("development", "test"),
            ),
        ),
        tools=(
            ToolRegistration(
                ref="tool://search@1",
                version="1",
                operation="builtin.search",
                description="Search the configured knowledge source.",
                risk=ToolRisk.LOW,
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {"query": {"type": "string"}},
                    "additionalProperties": False,
                },
                outputSchema={
                    "type": "object",
                    "required": ["items"],
                    "properties": {"items": {"type": "array"}},
                },
                idempotent=True,
                sideEffecting=False,
                costUsd=0.001,
                recoveryPolicy="idempotent",
            ),
            ToolRegistration(
                ref="tool://publish-report@1",
                version="1",
                operation="builtin.publish_report",
                description="Publish an approved report to the controlled business sink.",
                risk=ToolRisk.HIGH,
                inputSchema={
                    "type": "object",
                    "required": ["reports"],
                    "properties": {"reports": {"type": "object"}},
                    "additionalProperties": False,
                },
                outputSchema={
                    "type": "object",
                    "required": ["publicationId", "reports"],
                    "properties": {
                        "publicationId": {"type": "string"},
                        "reports": {"type": "object"},
                    },
                },
                idempotent=True,
                sideEffecting=True,
                costUsd=0.01,
                recoveryPolicy="compensate",
                compensationOperation="builtin.unpublish_report",
            ),
        ),
    )
