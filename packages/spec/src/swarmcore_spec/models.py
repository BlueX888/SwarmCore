from __future__ import annotations

import re
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator, model_validator

JsonSchema = dict[str, Any]
TemplateValue = Any
_DURATION = re.compile(r"^P(?=\d|T\d)(?:\d+D)?(?:T(?:\d+H)?(?:\d+M)?(?:\d+(?:\.\d+)?S)?)?$")
_RESOURCE_REF = re.compile(r"^(?:model|tool|agent|team|knowledge)://[^\s]+$")
_KEY = re.compile(r"^[a-z][a-z0-9_-]{0,62}$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Metadata(StrictModel):
    name: str = Field(min_length=1, max_length=128)
    labels: dict[str, str] = Field(default_factory=dict)


class RetryPolicy(StrictModel):
    max_attempts: int = Field(default=3, alias="maxAttempts", ge=1, le=20)
    initial_interval: str = Field(default="PT1S", alias="initialInterval")
    maximum_interval: str = Field(default="PT1M", alias="maximumInterval")
    backoff_coefficient: float = Field(default=2.0, alias="backoffCoefficient", ge=1, le=10)

    @field_validator("initial_interval", "maximum_interval")
    @classmethod
    def duration_is_iso8601(cls, value: str) -> str:
        if not _DURATION.fullmatch(value):
            raise ValueError("must be a positive ISO-8601 duration")
        return value


class Defaults(StrictModel):
    model: str | None = None
    timeout: str = "PT15M"
    retry_policy: str | RetryPolicy = Field(default="standard", alias="retryPolicy")

    @field_validator("timeout")
    @classmethod
    def timeout_is_iso8601(cls, value: str) -> str:
        if not _DURATION.fullmatch(value):
            raise ValueError("must be a positive ISO-8601 duration")
        return value

    @field_validator("model")
    @classmethod
    def model_ref_is_valid(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith("model://"):
            raise ValueError("must use a model:// reference")
        return value


class Budget(StrictModel):
    max_duration: str = Field(default="PT60M", alias="maxDuration")
    max_tokens: int = Field(default=1_000_000, alias="maxTokens", ge=1, le=1_000_000)
    max_cost_usd: float = Field(default=25, alias="maxCostUsd", gt=0, le=25)
    max_agents: int = Field(default=32, alias="maxAgents", ge=1, le=32)
    max_parallelism: int = Field(default=8, alias="maxParallelism", ge=1, le=8)
    on_exhausted: Literal[
        "fail", "partial_result", "wait_for_budget_approval"
    ] = Field(default="fail", alias="onExhausted")

    @field_validator("max_duration")
    @classmethod
    def duration_is_iso8601(cls, value: str) -> str:
        if not _DURATION.fullmatch(value):
            raise ValueError("must be a positive ISO-8601 duration")
        return value

    @model_validator(mode="after")
    def parallelism_does_not_exceed_agents(self) -> Budget:
        if self.max_parallelism > self.max_agents:
            raise ValueError("maxParallelism cannot exceed maxAgents")
        return self


class AgentSpec(StrictModel):
    ref: str | None = None
    role: str | None = Field(default=None, min_length=1, max_length=128)
    instructions: str | None = Field(default=None, min_length=1, max_length=100_000)
    model: str | None = None
    tools: list[str] = Field(default_factory=list)
    output_schema_ref: str | None = Field(default=None, alias="outputSchemaRef")

    @model_validator(mode="after")
    def inline_or_registered(self) -> AgentSpec:
        if self.ref is None and (self.role is None or self.instructions is None):
            raise ValueError("inline agents require role and instructions")
        if self.ref is not None and not self.ref.startswith("agent://"):
            raise ValueError("ref must use an agent:// reference")
        return self

    @field_validator("model")
    @classmethod
    def model_ref_is_valid(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith("model://"):
            raise ValueError("must use a model:// reference")
        return value

    @field_validator("tools")
    @classmethod
    def tool_refs_are_valid(cls, value: list[str]) -> list[str]:
        if any(not item.startswith("tool://") for item in value):
            raise ValueError("tools must use tool:// references")
        if len(value) != len(set(value)):
            raise ValueError("tools must be unique")
        return value


class NodeBase(StrictModel):
    depends_on: list[str] = Field(default_factory=list, alias="dependsOn")
    input: dict[str, TemplateValue] = Field(default_factory=dict)
    timeout: str | None = None
    retry_policy: str | RetryPolicy | None = Field(default=None, alias="retryPolicy")

    @field_validator("timeout")
    @classmethod
    def timeout_is_iso8601(cls, value: str | None) -> str | None:
        if value is not None and not _DURATION.fullmatch(value):
            raise ValueError("must be a positive ISO-8601 duration")
        return value


class AgentNode(NodeBase):
    type: Literal["agent"]
    agent: str
    fallback_agent: str | None = Field(default=None, alias="fallbackAgent")


class TeamNode(NodeBase):
    type: Literal["team"]
    team: str


class ToolNode(NodeBase):
    type: Literal["tool"]
    tool: str

    @field_validator("tool")
    @classmethod
    def tool_ref_is_valid(cls, value: str) -> str:
        if not value.startswith("tool://"):
            raise ValueError("must use a tool:// reference")
        return value


class TransformNode(NodeBase):
    type: Literal["transform"]
    expression: str | None = None
    transform: str | None = None

    @model_validator(mode="after")
    def has_one_transform(self) -> TransformNode:
        if (self.expression is None) == (self.transform is None):
            raise ValueError("exactly one of expression or transform is required")
        return self


class RouterRoute(StrictModel):
    when: str
    target: str


class RouterNode(NodeBase):
    type: Literal["router"]
    routes: list[RouterRoute] = Field(min_length=1)
    default: str | None = None


class ParallelNode(NodeBase):
    type: Literal["parallel"]
    branches: list[str] = Field(min_length=1)


class JoinNode(NodeBase):
    type: Literal["join"]
    strategy: Literal["all", "any", "quorum", "first_success"] = "all"
    quorum: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def valid_quorum(self) -> JoinNode:
        if self.strategy == "quorum" and self.quorum is None:
            raise ValueError("quorum is required for quorum strategy")
        if self.strategy != "quorum" and self.quorum is not None:
            raise ValueError("quorum is only valid for quorum strategy")
        return self


class LoopNode(NodeBase):
    type: Literal["loop"]
    body: list[str] = Field(min_length=1)
    until: str
    max_iterations: int = Field(alias="maxIterations", ge=1, le=20)

    @field_validator("body")
    @classmethod
    def body_nodes_are_unique(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            raise ValueError("loop body nodes must be unique")
        return value


class ApprovalNode(NodeBase):
    type: Literal["approval"]
    prompt: str = Field(min_length=1)
    input_schema: JsonSchema = Field(
        default_factory=lambda: {"type": "object"}, alias="inputSchema"
    )


class ExternalInputNode(NodeBase):
    type: Literal["input"]
    prompt: str = Field(min_length=1)
    input_schema: JsonSchema = Field(
        default_factory=lambda: {"type": "object"}, alias="inputSchema"
    )


class ReducerNode(NodeBase):
    type: Literal["reducer"]
    reducer: Literal["merge_object", "concat", "first_success", "vote"]


class SubflowNode(NodeBase):
    type: Literal["subflow"]
    strategy: str


class EmitNode(NodeBase):
    type: Literal["emit"]
    event: str = Field(min_length=1)
    payload: dict[str, TemplateValue] = Field(default_factory=dict)


Node = Annotated[
    AgentNode
    | TeamNode
    | ToolNode
    | TransformNode
    | RouterNode
    | ParallelNode
    | JoinNode
    | LoopNode
    | ApprovalNode
    | ExternalInputNode
    | ReducerNode
    | SubflowNode
    | EmitNode,
    Field(discriminator="type"),
]


class NodeMap(RootModel[dict[str, Node]]):
    @model_validator(mode="after")
    def keys_are_valid(self) -> NodeMap:
        invalid = [key for key in self.root if not _KEY.fullmatch(key)]
        if invalid:
            raise ValueError(f"invalid node keys: {', '.join(sorted(invalid))}")
        return self


class Graph(StrictModel):
    entrypoint: str
    nodes: NodeMap
    output: dict[str, TemplateValue]


class SwarmStrategy(StrictModel):
    api_version: Literal["swarmcore.io/v1"] = Field(alias="apiVersion")
    kind: Literal["SwarmStrategy"]
    metadata: Metadata
    spec: StrategySpec


class StrategySpec(StrictModel):
    input_schema: JsonSchema = Field(alias="inputSchema")
    output_schema: JsonSchema = Field(alias="outputSchema")
    defaults: Defaults = Field(default_factory=Defaults)
    budget: Budget = Field(default_factory=Budget)
    agents: dict[str, AgentSpec] = Field(default_factory=dict)
    graph: Graph
    definitions: dict[str, Any] = Field(default_factory=dict, alias="$defs")

    @field_validator("agents")
    @classmethod
    def agent_keys_are_valid(cls, value: dict[str, AgentSpec]) -> dict[str, AgentSpec]:
        invalid = [key for key in value if not _KEY.fullmatch(key)]
        if invalid:
            raise ValueError(f"invalid agent keys: {', '.join(sorted(invalid))}")
        return value


def is_resource_ref(value: str) -> bool:
    return bool(_RESOURCE_REF.fullmatch(value))
