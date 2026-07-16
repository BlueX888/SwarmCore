from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated, Any
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from swarmcore_application import (
    CapabilityCatalogService,
    CompilationService,
    RunNotTerminalError,
    RunQueryService,
    RunResultService,
    RunService,
    StrategyService,
)
from swarmcore_persistence import tenant_transaction

from .schemas import JsonRpcRequest

router = APIRouter()
_PROTOCOL_VERSION = "2025-11-25"
_strategies = StrategyService()
_runs = RunService()
_run_queries = RunQueryService()
_run_results = RunResultService()
_capabilities = CapabilityCatalogService()
_compilation = CompilationService(_strategies)

_TOOLS = [
    {
        "name": "swarm.capabilities.get",
        "description": "Return the allowed Agent, Tool, Model, node, schema, and limit catalog.",
        "inputSchema": {
            "type": "object",
            "required": ["projectId"],
            "properties": {"projectId": {"type": "string", "format": "uuid"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "swarm.strategy.validate",
        "description": "Validate an inline SwarmSpec v1 strategy.",
        "inputSchema": {
            "type": "object",
            "required": ["projectId", "spec"],
            "properties": {
                "projectId": {"type": "string", "format": "uuid"},
                "spec": {"type": "object"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "swarm.strategy.compile",
        "description": "Validate and compile an inline SwarmSpec v1 strategy.",
        "inputSchema": {
            "type": "object",
            "required": ["projectId", "spec"],
            "properties": {
                "projectId": {"type": "string", "format": "uuid"},
                "spec": {"type": "object"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "swarm.run.create",
        "description": "Durably accept a Run from a version or inline SwarmSpec.",
        "inputSchema": {
            "type": "object",
            "required": ["projectId", "input", "idempotencyKey"],
            "properties": {
                "projectId": {"type": "string", "format": "uuid"},
                "strategyVersionId": {"type": "string", "format": "uuid"},
                "spec": {"type": "object"},
                "input": {"type": "object"},
                "idempotencyKey": {"type": "string", "minLength": 1, "maxLength": 256},
            },
            "oneOf": [{"required": ["strategyVersionId"]}, {"required": ["spec"]}],
            "additionalProperties": False,
        },
    },
    {
        "name": "swarm.run.start",
        "description": "Durably accept a new SwarmCore Run.",
        "inputSchema": {
            "type": "object",
            "required": ["projectId", "input", "idempotencyKey"],
            "properties": {
                "projectId": {"type": "string", "format": "uuid"},
                "strategyVersionId": {"type": "string", "format": "uuid"},
                "spec": {"type": "object"},
                "input": {"type": "object"},
                "idempotencyKey": {"type": "string", "minLength": 1, "maxLength": 256},
            },
            "oneOf": [
                {"required": ["strategyVersionId"]},
                {"required": ["spec"]},
            ],
            "additionalProperties": False,
        },
    },
    {
        "name": "swarm.run.status",
        "description": "Return a Run product-state snapshot.",
        "inputSchema": {
            "type": "object",
            "required": ["projectId", "runId"],
            "properties": {
                "projectId": {"type": "string", "format": "uuid"},
                "runId": {"type": "string", "format": "uuid"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "swarm.run.get",
        "description": "Return a Run product-state snapshot.",
        "inputSchema": {
            "type": "object",
            "required": ["projectId", "runId"],
            "properties": {
                "projectId": {"type": "string", "format": "uuid"},
                "runId": {"type": "string", "format": "uuid"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "swarm.run.result",
        "description": "Return the stable terminal RunResult envelope.",
        "inputSchema": {
            "type": "object",
            "required": ["projectId", "runId"],
            "properties": {
                "projectId": {"type": "string", "format": "uuid"},
                "runId": {"type": "string", "format": "uuid"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "swarm.run.control",
        "description": "Durably apply a Run control command.",
        "inputSchema": {
            "type": "object",
            "required": ["projectId", "runId", "action", "idempotencyKey"],
            "properties": {
                "projectId": {"type": "string", "format": "uuid"},
                "runId": {"type": "string", "format": "uuid"},
                "action": {
                    "type": "string",
                    "enum": [
                        "pause",
                        "resume",
                        "cancel",
                        "approve",
                        "reject",
                        "provide_input",
                        "retry_task",
                    ],
                },
                "data": {"type": "object"},
                "idempotencyKey": {"type": "string", "minLength": 1, "maxLength": 256},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "swarm.run.cancel",
        "description": "Durably request Run cancellation.",
        "inputSchema": {
            "type": "object",
            "required": ["projectId", "runId", "idempotencyKey"],
            "properties": {
                "projectId": {"type": "string", "format": "uuid"},
                "runId": {"type": "string", "format": "uuid"},
                "idempotencyKey": {"type": "string", "minLength": 1, "maxLength": 256},
            },
            "additionalProperties": False,
        },
    },
]


@router.post("/mcp")
async def mcp_post(
    request: Request,
    body: JsonRpcRequest,
    tenant_id: Annotated[UUID, Header(alias="X-Tenant-ID")],
    protocol_version: Annotated[str | None, Header(alias="Mcp-Protocol-Version")] = None,
) -> JSONResponse:
    if body.method == "initialize":
        return _result(
            body.id,
            {
                "protocolVersion": _PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "SwarmCore", "version": "0.1.0"},
            },
        )
    if protocol_version != _PROTOCOL_VERSION:
        return _error(body.id, -32602, "unsupported or missing Mcp-Protocol-Version")
    if body.method == "notifications/initialized":
        return JSONResponse(content={}, status_code=202)
    if body.method == "tools/list":
        return _result(body.id, {"tools": _TOOLS})
    if body.method != "tools/call":
        return _error(body.id, -32601, "method not found")

    name = body.params.get("name")
    arguments = body.params.get("arguments", {})
    if not isinstance(name, str) or not isinstance(arguments, dict):
        return _error(body.id, -32602, "invalid tools/call parameters")
    try:
        structured = await _call_tool(request, tenant_id, name, arguments)
        return _result(
            body.id,
            {
                "content": [{"type": "text", "text": "SwarmCore operation accepted."}],
                "structuredContent": structured,
                "isError": False,
            },
        )
    except (LookupError, RunNotTerminalError, ValueError) as exc:
        code = _application_error_code(exc)
        return _result(
            body.id,
            {
                "content": [{"type": "text", "text": str(exc)}],
                "structuredContent": {"code": code, "detail": str(exc)},
                "isError": True,
            },
        )


@router.get("/mcp")
async def mcp_get() -> StreamingResponse:
    async def empty_stream() -> AsyncIterator[str]:
        yield ": connected\n\n"

    return StreamingResponse(empty_stream(), media_type="text/event-stream")


@router.delete("/mcp", status_code=204)
async def mcp_delete() -> Response:
    return Response(status_code=204)


async def _call_tool(
    request: Request, tenant_id: UUID, name: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    project_id = UUID(str(arguments["projectId"]))
    if name == "swarm.capabilities.get":
        return _capabilities.get().model_dump(mode="json", by_alias=True)
    if name == "swarm.strategy.validate":
        return _compilation.validate(arguments["spec"]).model_dump(mode="json", by_alias=True)
    if name == "swarm.strategy.compile":
        compile_result = _compilation.compile(arguments["spec"])
        payload = compile_result.model_dump(mode="json", by_alias=True)
        if compile_result.plan is not None:
            payload["planHash"] = compile_result.plan["plan_hash"]
        return payload

    database = request.app.state.database
    async with tenant_transaction(
        database.sessions, tenant_id=tenant_id, project_id=project_id
    ) as session:
        if name in {"swarm.run.create", "swarm.run.start"}:
            if "spec" in arguments:
                run, command = await _runs.create_inline(
                    session,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    raw_spec=arguments["spec"],
                    input_data=arguments["input"],
                    idempotency_key=str(arguments["idempotencyKey"]),
                )
            else:
                run, command = await _runs.create(
                    session,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    strategy_version_id=UUID(str(arguments["strategyVersionId"])),
                    input_data=arguments["input"],
                    idempotency_key=str(arguments["idempotencyKey"]),
                )
            return {
                "runId": str(run.id),
                "status": run.status,
                "commandId": str(command.id),
                "commandStatus": command.status,
                "planHash": run.plan_hash,
            }
        run_id = UUID(str(arguments["runId"]))
        if name in {"swarm.run.get", "swarm.run.status"}:
            return await _run_queries.get_snapshot(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
            )
        if name == "swarm.run.result":
            run_result = await _run_results.get(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
            )
            return run_result.model_dump(mode="json", by_alias=True)
        if name == "swarm.run.control":
            action = str(arguments["action"])
            allowed = {
                "pause",
                "resume",
                "cancel",
                "approve",
                "reject",
                "provide_input",
                "retry_task",
            }
            if action not in allowed:
                raise ValueError("unsupported control action")
            request_id = uuid5(
                NAMESPACE_URL,
                f"{tenant_id}:{run_id}:{arguments['idempotencyKey']}",
            )
            command = await _runs.commands.append(
                session,
                tenant_id=tenant_id,
                run_id=run_id,
                command_type=action,
                request_id=request_id,
                payload=dict(arguments.get("data", {})),
            )
            return {
                "commandId": str(command.id),
                "requestId": str(command.request_id),
                "commandSeq": command.command_seq,
                "status": command.status,
            }
        if name == "swarm.run.cancel":
            request_id = uuid5(
                NAMESPACE_URL,
                f"{tenant_id}:{run_id}:{arguments['idempotencyKey']}",
            )
            command = await _runs.commands.append(
                session,
                tenant_id=tenant_id,
                run_id=run_id,
                command_type="cancel",
                request_id=request_id,
                payload={},
            )
            return {
                "commandId": str(command.id),
                "requestId": str(command.request_id),
                "commandSeq": command.command_seq,
                "status": command.status,
            }
    raise ValueError(f"unknown tool: {name}")


def _result(request_id: str | int | None, result: dict[str, Any]) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": result})


def _error(request_id: str | int | None, code: int, message: str) -> JSONResponse:
    return JSONResponse(
        {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
    )


def _application_error_code(exc: Exception) -> str:
    if isinstance(exc, LookupError):
        return "NOT_FOUND"
    if isinstance(exc, RunNotTerminalError):
        return "RUN_NOT_TERMINAL"
    if str(exc) == "IDEMPOTENCY_KEY_REUSED":
        return "IDEMPOTENCY_KEY_REUSED"
    return "VALIDATION_ERROR"
