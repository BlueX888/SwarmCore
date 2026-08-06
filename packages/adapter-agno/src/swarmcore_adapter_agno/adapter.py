from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import Any, Protocol, cast

from jsonschema import Draft202012Validator, ValidationError

from agno.agent import Agent
from agno.models.base import Model
from agno.run.agent import RunOutput

logger = logging.getLogger(__name__)


class ModelResolver(Protocol):
    def resolve(self, reference: str, context: Mapping[str, Any]) -> Model | str: ...


class GatewayProxyFactory(Protocol):
    def create(self, tool_ref: str, capability_token: str, context: Mapping[str, Any]) -> Any: ...


class AgnoAdapter:
    """Narrow Agno boundary; raw external tools are never injected into an Agent."""

    def __init__(
        self,
        model_resolver: ModelResolver,
        gateway_proxies: GatewayProxyFactory | None = None,
    ) -> None:
        self._models = model_resolver
        self._gateway_proxies = gateway_proxies

    async def execute(self, request: Mapping[str, Any]) -> dict[str, Any]:
        agent_spec = cast(dict[str, Any], request["agent"])
        run = cast(dict[str, Any], request["run"])
        node = cast(dict[str, Any], request["node"])
        model_ref = agent_spec.get("model") or request.get("defaultModel")
        if not isinstance(model_ref, str):
            raise ValueError("agent has no resolved model reference")

        tool_refs = [str(item) for item in agent_spec.get("tools", [])]
        capability_tokens = cast(dict[str, str], request.get("toolCapabilities", {}))
        if tool_refs and self._gateway_proxies is None:
            raise ValueError("agent tools require the configured Tool Gateway proxy")
        tools = [
            self._gateway_proxies.create(tool_ref, capability_tokens[tool_ref], request)
            for tool_ref in tool_refs
            if self._gateway_proxies is not None
        ]
        output_schema = agent_spec.get("outputSchema")
        agent = Agent(
            id=f"{run['runId']}:{node['key']}",
            model=self._models.resolve(model_ref, request),
            role=str(agent_spec["role"]),
            instructions=str(agent_spec["instructions"]),
            tools=tools,
            output_schema=output_schema,
            use_json_mode=output_schema is not None,
        )
        output = await agent.arun(
            json.dumps(self._build_input(request), sort_keys=True),
            stream=False,
            run_id=str(request["taskExecutionId"]),
            session_id=str(request["agentInstanceId"]),
        )
        if not isinstance(output, RunOutput):
            raise TypeError("Agno returned a streaming result for a non-streaming call")
        status = getattr(output.status, "value", output.status)
        if isinstance(status, str) and status.upper() == "ERROR":
            detail = _error_detail(output)
            raise ValueError(f"model invocation failed: {detail}")
        if output.active_requirements:
            return {
                "status": "SUSPENDED",
                "runId": output.run_id,
                "requirements": [item.to_dict() for item in output.active_requirements],
            }
        content, content_source = self._extract_final_content(output)
        metrics = self._extract_metrics(output)
        logger.info(
            "agno_response_diagnostic %s",
            json.dumps(
                {
                    "runId": output.run_id,
                    "model": output.model,
                    "status": str(output.status) if output.status is not None else None,
                    "contentSource": content_source,
                    "contentType": type(content).__name__ if content is not None else None,
                    "contentLength": (
                        len(content) if isinstance(content, str | list | dict) else None
                    ),
                    "reasoningPresent": self._has_content(output.reasoning_content),
                    "providerDataKeys": sorted((output.model_provider_data or {}).keys()),
                    "messageRoles": [str(message.role) for message in (output.messages or [])],
                    "metrics": metrics,
                },
                sort_keys=True,
            ),
        )
        if not self._has_content(content):
            raise ValueError("model returned no final answer")
        if output_schema is not None:
            content = self._coerce_structured_content(content)
            try:
                Draft202012Validator(output_schema).validate(content)
            except ValidationError as exc:
                fallback = agent_spec.get("outputSchemaFallback")
                if isinstance(fallback, dict):
                    Draft202012Validator(output_schema).validate(fallback)
                    logger.warning(
                        "agent_output_schema_fallback node=%s validation_error=%s",
                        node.get("key"),
                        exc.message,
                    )
                    content = fallback
                else:
                    path = ".".join(str(part) for part in exc.absolute_path) or "$"
                    raise ValueError(
                        f"agent output does not match output schema at {path}: {exc.message}"
                    ) from exc
        return {
            "status": "COMPLETED",
            "content": content,
            "runId": output.run_id,
            "model": output.model,
            "metrics": metrics,
        }

    @staticmethod
    def _coerce_structured_content(content: Any) -> Any:
        """Parse JSON strings; treat non-JSON banners as model invocation failures."""
        if not isinstance(content, str):
            return content
        stripped = content.strip()
        if not stripped:
            raise ValueError("model returned no final answer")
        try:
            return json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"model invocation failed: {stripped[:500]}") from exc

    @classmethod
    def _extract_final_content(cls, output: RunOutput) -> tuple[Any, str | None]:
        """Extract only user-visible answer content, never the separate reasoning field."""
        if cls._has_content(output.content):
            return output.content, "content"

        reasoning = (
            output.reasoning_content.strip() if isinstance(output.reasoning_content, str) else None
        )
        for message in reversed(output.messages or []):
            if str(message.role).lower() != "assistant":
                continue
            candidate = cls._message_content(message.content)
            if cls._has_content(candidate) and not (
                isinstance(candidate, str) and reasoning and candidate.strip() == reasoning
            ):
                return candidate, "assistant_message.content"
        return None, None

    @staticmethod
    def _message_content(content: Any) -> Any:
        if not isinstance(content, list):
            return content
        text_parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                text_parts.append(part)
            elif isinstance(part, dict) and part.get("type") in {"text", "output_text"}:
                text = part.get("text")
                if isinstance(text, str):
                    text_parts.append(text)
            elif getattr(part, "type", None) in {"text", "output_text"}:
                text = getattr(part, "text", None)
                if isinstance(text, str):
                    text_parts.append(text)
        return "".join(text_parts)

    @staticmethod
    def _has_content(content: Any) -> bool:
        if content is None:
            return False
        if isinstance(content, str):
            return bool(content.strip())
        return True

    @staticmethod
    def _extract_metrics(output: RunOutput) -> dict[str, int | float]:
        if output.metrics is None:
            return {}
        metrics: dict[str, int | float] = {
            "input_tokens": output.metrics.input_tokens,
            "output_tokens": output.metrics.output_tokens,
        }
        if isinstance(output.metrics.cost, int | float) and not isinstance(
            output.metrics.cost, bool
        ):
            metrics["cost_usd"] = output.metrics.cost
        return metrics

    @staticmethod
    def _build_input(request: Mapping[str, Any]) -> dict[str, Any]:
        node = cast(dict[str, Any], request["node"])
        node_input = dict(node.get("config", {}).get("input", {}))
        context_mode = node_input.pop("_contextMode", "full")
        if context_mode not in {"full", "node_only"}:
            raise ValueError(f"unsupported agent context mode: {context_mode}")
        if context_mode == "node_only":
            return {
                "input": {},
                "nodeInput": node_input,
                "dependencyOutputs": {},
            }
        return {
            "input": cast(dict[str, Any], request["run"]).get("input", {}),
            "nodeInput": node_input,
            "dependencyOutputs": request.get("dependencyOutputs", {}),
        }


def _error_detail(output: RunOutput) -> str:
    content = output.content
    if isinstance(content, str) and content.strip():
        return content.strip()
    if content is not None:
        return str(content)
    return str(output.status)
