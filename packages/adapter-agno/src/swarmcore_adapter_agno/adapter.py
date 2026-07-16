from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, cast

from jsonschema import Draft202012Validator, ValidationError

from agno.agent import Agent
from agno.models.base import Model
from agno.run.agent import RunOutput


class ModelResolver(Protocol):
    def resolve(self, reference: str) -> Model | str: ...


class AgnoAdapter:
    """Narrow Agno boundary; raw external tools are never injected into an Agent."""

    def __init__(self, model_resolver: ModelResolver) -> None:
        self._models = model_resolver

    async def execute(self, request: Mapping[str, Any]) -> dict[str, Any]:
        agent_spec = cast(dict[str, Any], request["agent"])
        run = cast(dict[str, Any], request["run"])
        node = cast(dict[str, Any], request["node"])
        model_ref = agent_spec.get("model") or request.get("defaultModel")
        if not isinstance(model_ref, str):
            raise ValueError("agent has no resolved model reference")

        agent = Agent(
            id=f"{run['runId']}:{node['key']}",
            model=self._models.resolve(model_ref),
            role=str(agent_spec["role"]),
            instructions=str(agent_spec["instructions"]),
            tools=[],
            output_schema=agent_spec.get("outputSchema"),
        )
        output = await agent.arun(
            self._build_input(request),
            stream=False,
            run_id=str(request["taskExecutionId"]),
            session_id=str(request["agentInstanceId"]),
        )
        if not isinstance(output, RunOutput):
            raise TypeError("Agno returned a streaming result for a non-streaming call")
        if output.active_requirements:
            return {
                "status": "SUSPENDED",
                "runId": output.run_id,
                "requirements": [item.to_dict() for item in output.active_requirements],
            }
        content = output.content
        output_schema = agent_spec.get("outputSchema")
        if output_schema is not None:
            try:
                Draft202012Validator(output_schema).validate(content)
            except ValidationError as exc:
                raise ValueError(
                    f"agent output does not match output schema: {exc.message}"
                ) from exc
        return {
            "status": "COMPLETED",
            "content": content,
            "runId": output.run_id,
            "model": output.model,
            "metrics": output.metrics.to_dict() if output.metrics else {},
        }

    @staticmethod
    def _build_input(request: Mapping[str, Any]) -> dict[str, Any]:
        node = cast(dict[str, Any], request["node"])
        return {
            "input": cast(dict[str, Any], request["run"]).get("input", {}),
            "nodeInput": node.get("config", {}).get("input", {}),
            "dependencyOutputs": request.get("dependencyOutputs", {}),
        }
