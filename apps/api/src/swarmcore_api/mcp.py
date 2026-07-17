from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from swarmcore_application import (
    CapabilityCatalogService,
    CompilationService,
    RunCommandConflictError,
    RunCommandService,
    RunNotTerminalError,
    RunQueryService,
    RunResultService,
    RunService,
    StrategyService,
)
from swarmcore_governance import (
    PolicyDenied,
    PolicyError,
    PolicyRequest,
    PolicySubject,
    redact_policy_log,
)
from swarmcore_persistence import AuditRepository, tenant_transaction
from swarmcore_persistence.errors import PersistenceConflictError
from swarmcore_persistence.models import Project

from .authentication import AuthenticationError, Identity, JwtAuthenticator
from .schemas import JsonRpcRequest

router = APIRouter()
_PROTOCOL_VERSION = "2025-11-25"
_strategies = StrategyService()
_runs = RunService()
_commands = RunCommandService()
_run_queries = RunQueryService()
_run_results = RunResultService()
_capabilities = CapabilityCatalogService()
_compilation = CompilationService(_strategies)
logger = logging.getLogger(__name__)

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
]


@router.post("/mcp")
async def mcp_post(
    request: Request,
    body: JsonRpcRequest,
    tenant_id: Annotated[UUID | None, Header(alias="X-Tenant-ID")] = None,
    protocol_version: Annotated[str | None, Header(alias="Mcp-Protocol-Version")] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    actor_id: Annotated[str, Header(alias="X-Actor-ID")] = "local-user",
    roles: Annotated[str, Header(alias="X-Roles")] = "tenant_admin",
    scopes: Annotated[str, Header(alias="X-Scopes")] = "",
) -> JSONResponse:
    settings = request.app.state.settings
    if settings.auth_mode == "jwt":
        try:
            authenticator = getattr(request.app.state, "jwt_authenticator", None)
            if authenticator is None:
                authenticator = JwtAuthenticator(settings)
                request.app.state.jwt_authenticator = authenticator
            identity = authenticator.authenticate(authorization or "")
        except AuthenticationError:
            return _error(body.id, -32001, "AUTHENTICATION_REQUIRED")
    else:
        if tenant_id is None:
            return _error(body.id, -32001, "AUTHENTICATION_REQUIRED")
        identity = Identity(
            subject_id=actor_id,
            tenant_id=tenant_id,
            roles=tuple(value.strip() for value in roles.split(",") if value.strip()),
            scopes=tuple(value.strip() for value in scopes.split(",") if value.strip()),
            issuer="local-development",
            audience="swarmcore-api",
            project_scopes=(),
        )
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
        structured = await _call_tool(request, identity, name, arguments)
        return _result(
            body.id,
            {
                "content": [{"type": "text", "text": "SwarmCore operation accepted."}],
                "structuredContent": structured,
                "isError": False,
            },
        )
    except (
        LookupError,
        PersistenceConflictError,
        RunCommandConflictError,
        RunNotTerminalError,
        PolicyError,
        ValueError,
    ) as exc:
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
    request: Request, identity: Identity, name: str, arguments: dict[str, Any]
) -> dict[str, Any]:
    tenant_id = identity.tenant_id
    project_id = UUID(str(arguments["projectId"]))
    if request.app.state.settings.auth_mode == "jwt" and not identity.can_access_project(
        project_id
    ):
        raise PolicyDenied("project scope does not grant access")
    effective_scopes = identity.scopes_for(project_id)
    action = {
        "swarm.capabilities.get": "run.read",
        "swarm.strategy.validate": "strategy.read",
        "swarm.strategy.compile": "strategy.write",
        "swarm.run.create": "run.create",
        "swarm.run.status": "run.read",
        "swarm.run.result": "run.read",
        "swarm.run.control": "run.control",
    }.get(name)
    if action is None:
        raise ValueError(f"unknown tool: {name}")
    policy_request = PolicyRequest(
        subject=PolicySubject(
            id=identity.subject_id,
            tenantId=str(identity.tenant_id),
            roles=identity.roles,
            scopes=effective_scopes,
        ),
        action=action,
        resource={"projectId": str(project_id), "protocol": "mcp"},
    )
    decision = await request.app.state.policy.evaluate(policy_request)
    if not decision.allow:
        request.app.state.metrics.policy_denied.add(1, {"action": action})
        logger.warning(
            "policy denied MCP tool",
            extra={"event": "policy.denied", "fields": redact_policy_log(policy_request, decision)},
        )
        if request.app.state.settings.policy_mode == "opa":
            database = request.app.state.database
            async with tenant_transaction(
                database.sessions, tenant_id=tenant_id, project_id=project_id
            ) as session:
                if await session.get(Project, project_id) is not None:
                    await AuditRepository().append(
                        session,
                        tenant_id=tenant_id,
                        project_id=project_id,
                        actor_id=identity.subject_id,
                        action="policy.deny",
                        resource_type="mcp_tool",
                        resource_id=name,
                        outcome="DENIED",
                        policy_revision=decision.policy_revision,
                        metadata={"requestedAction": action},
                    )
    decision.enforce()
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
        if name == "swarm.run.create":
            if "spec" in arguments:
                run, command = await _runs.create_inline(
                    session,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    raw_spec=arguments["spec"],
                    input_data=arguments["input"],
                    idempotency_key=str(arguments["idempotencyKey"]),
                    initiated_by=identity.subject_id,
                    submitted_scopes=effective_scopes,
                    auth_context_hash=identity.context_hash,
                )
            else:
                run, command = await _runs.create(
                    session,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    strategy_version_id=UUID(str(arguments["strategyVersionId"])),
                    input_data=arguments["input"],
                    idempotency_key=str(arguments["idempotencyKey"]),
                    initiated_by=identity.subject_id,
                    submitted_scopes=effective_scopes,
                    auth_context_hash=identity.context_hash,
                )
            return {
                "runId": str(run.id),
                "status": run.status,
                "commandId": str(command.id),
                "commandStatus": command.status,
                "planHash": run.plan_hash,
            }
        run_id = UUID(str(arguments["runId"]))
        if name == "swarm.run.status":
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
            handle = await _commands.append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=run_id,
                command_type=action,
                idempotency_key=str(arguments["idempotencyKey"]),
                payload=dict(arguments.get("data", {})),
                actor=identity.subject_id,
            )
            return handle.model_dump(mode="json", by_alias=True)
    raise ValueError(f"unknown tool: {name}")


def _result(request_id: str | int | None, result: dict[str, Any]) -> JSONResponse:
    return JSONResponse({"jsonrpc": "2.0", "id": request_id, "result": result})


def _error(request_id: str | int | None, code: int, message: str) -> JSONResponse:
    return JSONResponse(
        {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}
    )


def _application_error_code(exc: Exception) -> str:
    if isinstance(exc, PolicyDenied):
        return "POLICY_DENIED"
    if isinstance(exc, PolicyError):
        return "POLICY_UNAVAILABLE"
    if isinstance(exc, LookupError):
        return "NOT_FOUND"
    if isinstance(exc, PersistenceConflictError | RunCommandConflictError):
        return "CONFLICT"
    if isinstance(exc, RunNotTerminalError):
        return "RUN_NOT_TERMINAL"
    if str(exc) == "IDEMPOTENCY_KEY_REUSED":
        return "IDEMPOTENCY_KEY_REUSED"
    return "VALIDATION_ERROR"
