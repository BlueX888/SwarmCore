from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field
from swarmcore_registry import builtin_registry
from swarmcore_spec.models import (
    AgentNode,
    AgentSpec,
    ApprovalNode,
    Budget,
    ExternalInputNode,
    JoinNode,
    LoopNode,
    ParallelNode,
    ReducerNode,
    RouterNode,
    SwarmStrategy,
    ToolNode,
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
        "router": RouterNode,
        "tool": ToolNode,
        "loop": LoopNode,
    }

    def get(self) -> CapabilityCatalog:
        registry = builtin_registry()
        return CapabilityCatalog(
            schemaVersion="swarmcore.io/capabilities/v1",
            registrySnapshot=registry.snapshot_id,
            agents=[
                AgentCapability(
                    id="inline/agno",
                    runtime="agno",
                    environments=["development", "production"],
                    declarationSchema=AgentSpec.model_json_schema(by_alias=True),
                ),
                *[
                    AgentCapability(
                        id=item.ref,
                        runtime="registry/agno",
                        environments=["development", "production"],
                        declarationSchema=AgentSpec.model_json_schema(by_alias=True),
                    )
                    for item in registry.agents
                ],
                AgentCapability(
                    id="inline/fake-deterministic",
                    runtime="fake-deterministic",
                    environments=["development", "test"],
                    declarationSchema=AgentSpec.model_json_schema(by_alias=True),
                ),
            ],
            tools=[
                ToolCapability(
                    ref=item.ref,
                    risk=item.risk.value,
                    inputSchema=item.input_schema,
                    outputSchema=item.output_schema,
                )
                for item in registry.tools
            ],
            models=[
                ModelCapability(
                    ref=item.ref,
                    runtime=item.runtime,
                    environments=list(item.environments),
                )
                for item in registry.models
            ],
            nodeTypes=[
                NodeCapability(type=name, schema=model.model_json_schema(by_alias=True))
                for name, model in sorted(self._NODE_TYPES.items())
            ],
            limits=Budget().model_dump(mode="json", by_alias=True),
            swarmSpecSchema=SwarmStrategy.model_json_schema(by_alias=True),
        )
