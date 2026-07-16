from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field
from swarmcore_spec.models import (
    AgentNode,
    AgentSpec,
    ApprovalNode,
    Budget,
    ExternalInputNode,
    JoinNode,
    ParallelNode,
    ReducerNode,
    SwarmStrategy,
)


class CapabilityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class AgentCapability(CapabilityModel):
    id: str
    runtime: str
    environments: list[str]
    declaration_schema: dict[str, object] = Field(alias="declarationSchema")


class ModelCapability(CapabilityModel):
    ref: str
    runtime: str
    environments: list[str]


class ToolCapability(CapabilityModel):
    ref: str
    risk: str
    input_schema: dict[str, object] = Field(alias="inputSchema")
    output_schema: dict[str, object] = Field(alias="outputSchema")


class NodeCapability(CapabilityModel):
    type: str
    config_schema: dict[str, object] = Field(alias="schema")


class CapabilityCatalog(CapabilityModel):
    schema_version: str = Field(alias="schemaVersion")
    registry_snapshot: str = Field(alias="registrySnapshot")
    agents: list[AgentCapability]
    tools: list[ToolCapability]
    models: list[ModelCapability]
    node_types: list[NodeCapability] = Field(alias="nodeTypes")
    limits: dict[str, object]
    swarm_spec_schema: dict[str, object] = Field(alias="swarmSpecSchema")


class CapabilityCatalogService:
    _NODE_TYPES: ClassVar[dict[str, type[BaseModel]]] = {
        "agent": AgentNode,
        "approval": ApprovalNode,
        "input": ExternalInputNode,
        "join": JoinNode,
        "parallel": ParallelNode,
        "reducer": ReducerNode,
    }

    def get(self) -> CapabilityCatalog:
        return CapabilityCatalog(
            schemaVersion="swarmcore.io/capabilities/v1",
            registrySnapshot="builtin:phase2b",
            agents=[
                AgentCapability(
                    id="inline/agno",
                    runtime="agno",
                    environments=["development", "production"],
                    declarationSchema=AgentSpec.model_json_schema(by_alias=True),
                ),
                AgentCapability(
                    id="inline/fake-deterministic",
                    runtime="fake-deterministic",
                    environments=["development", "test"],
                    declarationSchema=AgentSpec.model_json_schema(by_alias=True),
                ),
            ],
            tools=[],
            models=[
                ModelCapability(
                    ref="model://general",
                    runtime="agno",
                    environments=["development", "production"],
                ),
                ModelCapability(
                    ref="model://fake-deterministic",
                    runtime="fake-deterministic",
                    environments=["development", "test"],
                ),
            ],
            nodeTypes=[
                NodeCapability(type=name, schema=model.model_json_schema(by_alias=True))
                for name, model in sorted(self._NODE_TYPES.items())
            ],
            limits=Budget().model_dump(mode="json", by_alias=True),
            swarmSpecSchema=SwarmStrategy.model_json_schema(by_alias=True),
        )
