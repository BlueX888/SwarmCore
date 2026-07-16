from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated, Any
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
from swarmcore_persistence import tenant_transaction
from swarmcore_persistence.models import Run

from .routes import _run_snapshot
from .schemas import JsonRpcRequest
from .services import RunService, StrategyService

router = APIRouter()
_PROTOCOL_VERSION = "2025-11-25"
_strategies = StrategyService()
_runs = RunService()

_TOOLS = [
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
        "name": "swarm.run.start",
        "description": "Durably accept a new SwarmCore Run.",
        "inputSchema": {
            "type": "object",
            "required": ["projectId", "strategyVersionId", "input", "idempotencyKey"],
            "properties": {
                "projectId": {"type": "string", "format": "uuid"},
                "strategyVersionId": {"type": "string", "format": "uuid"},
                "input": {"type": "object"},
                "idempotencyKey": {"type": "string", "minLength": 1, "maxLength": 256},
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
    authorization: Annotated[str, Header(alias="Authorization")],
    protocol_version: Annotated[str | None, Header(alias="Mcp-Protocol-Version")] = None,
) -> JSONResponse:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer authentication is required")
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
    except (LookupError, ValueError) as exc:
        return _result(
            body.id,
            {
                "content": [{"type": "text", "text": str(exc)}],
                "structuredContent": {"code": type(exc).__name__, "detail": str(exc)},
                "isError": True,
            },
        )


@router.get("/mcp")
async def mcp_get(
    authorization: Annotated[str, Header(alias="Authorization")],
) -> StreamingResponse:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer authentication is required")

    async def empty_stream() -> AsyncIterator[str]:
        yield ": connected\n\n"

    return StreamingResponse(empty_stream(), media_type="text/event-stream")


@router.delete("/mcp", status_code=204)
async def mcp_delete(
    authorization: Annotated[str, Header(alias="Authorization")],
) -> Response:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer authentication is required")
    return Response(status_code=204)


async def _call_tool(
    request: Request, tenant_id: UUID, name: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    project_id = UUID(str(arguments["projectId"]))
    if name == "swarm.strategy.compile":
        _, plan = _strategies.compile(
            arguments["spec"], registry_snapshot="mcp:inline", policy_revision="phase1"
        )
        return {"valid": True, "planHash": plan.plan_hash, "plan": plan.model_dump(mode="json")}

    database = request.app.state.database
    async with tenant_transaction(
        database.sessions, tenant_id=tenant_id, project_id=project_id
    ) as session:
        if name == "swarm.run.start":
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
            }
        run_id = UUID(str(arguments["runId"]))
        if name == "swarm.run.get":
            queried_run = await session.scalar(
                select(Run).where(Run.id == run_id, Run.tenant_id == tenant_id)
            )
            if queried_run is None or queried_run.project_id != project_id:
                raise LookupError("run not found")
            return _run_snapshot(queried_run).model_dump(mode="json", by_alias=True)
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
