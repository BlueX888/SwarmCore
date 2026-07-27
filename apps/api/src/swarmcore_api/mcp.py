from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Annotated, Any, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from swarmcore_application import (
    CapabilityCatalogService,
    CapabilityCenterService,
    CaseSubjectInput,
    CompilationService,
    InvoiceBatchInput,
    RunCommandConflictError,
    RunCommandService,
    RunNotTerminalError,
    RunQueryService,
    RunResultService,
    RunService,
    StrategyService,
)
from swarmcore_capability_contract_integrity import MANIFEST, MANIFEST_V2, MANIFEST_V2_1
from swarmcore_capability_contract_post_evaluation import MANIFEST as POST_EVALUATION_MANIFEST
from swarmcore_capability_deviation_analysis import MANIFEST as DEVIATION_ANALYSIS_MANIFEST
from swarmcore_capability_invoice_assurance import MANIFEST as INVOICE_ASSURANCE_MANIFEST
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
from .business_routes import (
    _assessment_detail,
    _business_work_snapshot,
    _invoice_batch_snapshot,
)
from .business_routes import business_objects as _business_objects
from .business_routes import business_works as _business_works
from .business_routes import capability_packs as _capability_packs
from .business_routes import cases as _cases
from .business_routes import documents as _documents
from .business_routes import invoice_assurance_operations as _invoice_assurance_operations
from .business_routes import workbench as _workbench
from .schemas import JsonRpcRequest

router = APIRouter()
_PROTOCOL_VERSION = "2025-11-25"
_strategies = StrategyService()
_runs = RunService()
_commands = RunCommandService()
_run_queries = RunQueryService()
_run_results = RunResultService()
_capabilities = CapabilityCatalogService(
    (
        MANIFEST,
        MANIFEST_V2,
        MANIFEST_V2_1,
        POST_EVALUATION_MANIFEST,
        DEVIATION_ANALYSIS_MANIFEST,
        INVOICE_ASSURANCE_MANIFEST,
    )
)
_compilation = CompilationService(_strategies)
logger = logging.getLogger(__name__)


def _business_schema(
    *,
    required: tuple[str, ...] = (),
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["projectId", *required],
        "properties": {
            "projectId": {"type": "string", "format": "uuid"},
            **(properties or {}),
        },
        "additionalProperties": False,
    }


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
    {
        "name": "list_capability_packs",
        "description": "List trusted capability pack versions and project enablement state.",
        "inputSchema": _business_schema(),
    },
    {
        "name": "list_business_works",
        "description": "List product business works with runnable status and blockers.",
        "inputSchema": _business_schema(),
    },
    {
        "name": "get_business_work",
        "description": "Get one business work summary, readiness, and configuration projection.",
        "inputSchema": _business_schema(
            required=("workKey",),
            properties={"workKey": {"type": "string"}},
        ),
    },
    {
        "name": "bind_business_work_strategy",
        "description": (
            "Bind a published execution strategy version to a business work and enable it."
        ),
        "inputSchema": _business_schema(
            required=("workKey", "strategyVersionId", "idempotencyKey"),
            properties={
                "workKey": {"type": "string"},
                "strategyVersionId": {"type": "string", "format": "uuid"},
                "idempotencyKey": {"type": "string"},
            },
        ),
    },
    {
        "name": "get_assessment",
        "description": "Get an assessment (evaluation) result with case context.",
        "inputSchema": _business_schema(
            required=("assessmentId",),
            properties={"assessmentId": {"type": "string", "format": "uuid"}},
        ),
    },
    {
        "name": "create_invoice_assurance_batch",
        "description": "Queue multiple invoice-assurance cases; every invoice remains an independent Case and Assessment.",
        "inputSchema": _business_schema(
            required=("items", "idempotencyKey"),
            properties={
                "items": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 100,
                    "items": {
                        "type": "object",
                        "required": ["payload", "subjects"],
                        "properties": {
                            "payload": {"type": "object"},
                            "subjects": {
                                "type": "array",
                                "minItems": 1,
                                "items": {
                                    "type": "object",
                                    "required": [
                                        "businessObjectId",
                                        "businessObjectVersionId",
                                        "role",
                                        "subjectKey",
                                    ],
                                    "properties": {
                                        "businessObjectId": {
                                            "type": "string",
                                            "format": "uuid",
                                        },
                                        "businessObjectVersionId": {
                                            "type": "string",
                                            "format": "uuid",
                                        },
                                        "role": {"type": "string"},
                                        "subjectKey": {"type": "string"},
                                    },
                                    "additionalProperties": False,
                                },
                            },
                            "owner": {"type": "string"},
                        },
                        "additionalProperties": False,
                    },
                },
                "maxParallelism": {"type": "integer", "minimum": 1, "maximum": 10},
                "idempotencyKey": {"type": "string", "minLength": 1, "maxLength": 256},
            },
        ),
    },
    {
        "name": "get_invoice_assurance_batch",
        "description": "Get aggregate and per-invoice status for an invoice-assurance batch.",
        "inputSchema": _business_schema(
            required=("batchId",),
            properties={"batchId": {"type": "string", "format": "uuid"}},
        ),
    },
    {
        "name": "get_invoice_assurance_rule_trends",
        "description": "Aggregate historical invoice-assurance outcomes and non-pass rule hits.",
        "inputSchema": _business_schema(
            properties={"bucket": {"enum": ["day", "week", "month"]}},
        ),
    },
    {
        "name": "create_work_item",
        "description": "Create a schema-validated business work item and immutable revision.",
        "inputSchema": _business_schema(
            required=("workItemType", "payload", "idempotencyKey"),
            properties={
                "workItemType": {"type": "string"},
                "payload": {"type": "object"},
                "owner": {"type": "string"},
                "idempotencyKey": {"type": "string"},
            },
        ),
    },
    {
        "name": "upsert_business_object",
        "description": "Create or idempotently version a project-scoped business object.",
        "inputSchema": _business_schema(
            required=("objectType", "canonicalKey", "schemaRef", "data"),
            properties={
                "objectType": {"type": "string"},
                "canonicalKey": {"type": "string"},
                "schemaRef": {"type": "string"},
                "data": {"type": "object"},
                "provenance": {"type": "object"},
            },
        ),
    },
    {
        "name": "create_case",
        "description": "Create a scenario case with immutable business object subjects.",
        "inputSchema": _business_schema(
            required=("scenarioType", "payload", "subjects", "idempotencyKey"),
            properties={
                "scenarioType": {"type": "string"},
                "payload": {"type": "object"},
                "subjects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": [
                            "businessObjectId",
                            "businessObjectVersionId",
                            "role",
                            "subjectKey",
                        ],
                        "properties": {
                            "businessObjectId": {"type": "string", "format": "uuid"},
                            "businessObjectVersionId": {
                                "type": "string",
                                "format": "uuid",
                            },
                            "role": {"type": "string"},
                            "subjectKey": {"type": "string"},
                        },
                        "additionalProperties": False,
                    },
                },
                "owner": {"type": "string"},
                "idempotencyKey": {"type": "string"},
            },
        ),
    },
    {
        "name": "assess_case",
        "description": "Durably accept a new assessment for the current case revision.",
        "inputSchema": _business_schema(
            required=("caseId", "idempotencyKey"),
            properties={
                "caseId": {"type": "string", "format": "uuid"},
                "idempotencyKey": {"type": "string"},
            },
        ),
    },
    {
        "name": "get_case_result",
        "description": "Return a case and its latest assessment result.",
        "inputSchema": _business_schema(
            required=("caseId",),
            properties={"caseId": {"type": "string", "format": "uuid"}},
        ),
    },
    {
        "name": "list_case_findings",
        "description": "List the current finding projection for a case.",
        "inputSchema": _business_schema(
            required=("caseId",),
            properties={"caseId": {"type": "string", "format": "uuid"}},
        ),
    },
    {
        "name": "execute_work_item",
        "description": "Create one Evaluation and Run for a work item revision.",
        "inputSchema": _business_schema(
            required=("workItemId", "idempotencyKey"),
            properties={
                "workItemId": {"type": "string", "format": "uuid"},
                "idempotencyKey": {"type": "string"},
            },
        ),
    },
    {
        "name": "get_evaluation",
        "description": "Get an Evaluation result and immutable provenance snapshot.",
        "inputSchema": _business_schema(
            required=("evaluationId",),
            properties={"evaluationId": {"type": "string", "format": "uuid"}},
        ),
    },
    {
        "name": "list_findings",
        "description": "List current findings for a work item.",
        "inputSchema": _business_schema(
            required=("workItemId",),
            properties={"workItemId": {"type": "string", "format": "uuid"}},
        ),
    },
    {
        "name": "act_on_finding",
        "description": "Acknowledge, assign, waive, resolve, or reopen a finding.",
        "inputSchema": _business_schema(
            required=("findingId", "action", "idempotencyKey"),
            properties={
                "findingId": {"type": "string", "format": "uuid"},
                "action": {
                    "type": "string",
                    "enum": ["ACKNOWLEDGE", "ASSIGN", "WAIVE", "RESOLVE", "REOPEN"],
                },
                "reason": {"type": "string"},
                "assignee": {"type": "string"},
                "idempotencyKey": {"type": "string"},
            },
        ),
    },
    {
        "name": "get_report",
        "description": "Get JSON and HTML reports for an Evaluation.",
        "inputSchema": _business_schema(
            required=("evaluationId",),
            properties={"evaluationId": {"type": "string", "format": "uuid"}},
        ),
    },
    {
        "name": "list_documents",
        "description": "List files in the project business document library.",
        "inputSchema": _business_schema(
            properties={
                "search": {"type": "string"},
                "category": {"type": "string"},
                "status": {"type": "string"},
            }
        ),
    },
]

_CAPABILITY_CENTER_TOOLS = [
    {
        "name": "swarm.capability-center.list",
        "description": "List project capabilities with runtime readiness.",
        "inputSchema": _business_schema(),
    },
    {
        "name": "swarm.capability.run",
        "description": "Create a standard durable Run for one ready capability.",
        "inputSchema": _business_schema(
            required=("capabilityRef", "input", "idempotencyKey"),
            properties={
                "capabilityRef": {"type": "string", "minLength": 1},
                "input": {"type": "object"},
                "presetId": {"type": "string", "format": "uuid"},
                "idempotencyKey": {"type": "string", "minLength": 1, "maxLength": 256},
            },
        ),
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
        tools = [*_TOOLS, *_CAPABILITY_CENTER_TOOLS] if settings.capability_center_v2 else _TOOLS
        return _result(body.id, {"tools": tools})
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
        "swarm.capability-center.list": "capability.read",
        "swarm.capability.run": "run.create",
        "swarm.strategy.validate": "strategy.read",
        "swarm.strategy.compile": "strategy.write",
        "swarm.run.create": "run.create",
        "swarm.run.status": "run.read",
        "swarm.run.result": "run.read",
        "swarm.run.control": "run.control",
        "list_capability_packs": "capability.read",
        "list_business_works": "capability.read",
        "get_business_work": "capability.read",
        "bind_business_work_strategy": "capability.manage",
        "get_assessment": "work-item.read",
        "create_invoice_assurance_batch": "case.assess",
        "get_invoice_assurance_batch": "case.read",
        "get_invoice_assurance_rule_trends": "case.read",
        "create_work_item": "work-item.write",
        "upsert_business_object": "business-object.write",
        "create_case": "case.write",
        "assess_case": "case.assess",
        "get_case_result": "case.read",
        "list_case_findings": "case.read",
        "execute_work_item": "work-item.execute",
        "get_evaluation": "work-item.read",
        "list_findings": "finding.read",
        "act_on_finding": "finding.act",
        "get_report": "report.read",
        "list_documents": "document.read",
    }.get(name)
    if action is None:
        raise ValueError(f"unknown tool: {name}")
    if name in {"swarm.capability-center.list", "swarm.capability.run"} and not (
        request.app.state.settings.capability_center_v2
    ):
        raise ValueError("capability center v2 is disabled")
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
    if name == "swarm.capability-center.list":
        center: CapabilityCenterService = request.app.state.capability_center
        database = request.app.state.database
        async with tenant_transaction(
            database.sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            items = await center.list(
                tenant_id=tenant_id,
                project_id=project_id,
                environment=request.app.state.settings.environment,
                session=session,
            )
        return {
            "registrySnapshot": center.registry_snapshot_id,
            "items": [item.model_dump(mode="json", by_alias=True) for item in items],
        }
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
        if name == "swarm.capability.run":
            center = request.app.state.capability_center
            preset_id = arguments.get("presetId")
            run, command = await center.run(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                environment=request.app.state.settings.environment,
                capability_ref=str(arguments["capabilityRef"]),
                input_data=dict(arguments["input"]),
                preset_id=UUID(str(preset_id)) if preset_id is not None else None,
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
        if name == "list_capability_packs":
            await _capability_packs.ensure_trusted(
                session, tenant_id=tenant_id, project_id=project_id
            )
            rows = await _capability_packs.list_project(
                session, tenant_id=tenant_id, project_id=project_id
            )
            pack_items: list[dict[str, Any]] = []
            for pack, version, binding in rows:
                blockers = await _capability_packs.blockers_for_version(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    version=version,
                    session=session,
                )
                pack_items.append(
                    {
                        "packId": str(pack.id),
                        "name": pack.name,
                        "versionId": str(version.id),
                        "version": version.version,
                        "contentHash": version.content_hash,
                        "manifest": version.manifest,
                        "enabled": binding is not None
                        and binding.status in {"ENABLED", "DEGRADED"},
                        "bindingStatus": binding.status if binding is not None else None,
                        "configuration": (
                            dict(binding.configuration) if binding is not None else {}
                        ),
                        "blockers": blockers,
                    }
                )
            return {"items": pack_items}
        if name == "list_business_works":
            work_summaries = await _business_works.list_works(
                session, tenant_id=tenant_id, project_id=project_id
            )
            return {
                "items": [
                    _business_work_snapshot(item).model_dump(by_alias=True, mode="json")
                    for item in work_summaries
                ]
            }
        if name == "get_business_work":
            summary = await _business_works.get_work(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                work_key=str(arguments["workKey"]),
            )
            return _business_work_snapshot(summary).model_dump(by_alias=True, mode="json")
        if name == "bind_business_work_strategy":
            summary = await _business_works.bind_strategy(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                work_key=str(arguments["workKey"]),
                strategy_version_id=UUID(str(arguments["strategyVersionId"])),
                idempotency_key=str(arguments["idempotencyKey"]),
                actor=identity.subject_id,
            )
            return _business_work_snapshot(summary).model_dump(by_alias=True, mode="json")
        if name == "get_assessment":
            evaluation, item, revision = await _business_works.get_assessment(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                assessment_id=UUID(str(arguments["assessmentId"])),
            )
            return _assessment_detail(evaluation, item, revision).model_dump(
                by_alias=True, mode="json"
            )
        if name == "create_invoice_assurance_batch":
            raw_items = arguments["items"]
            if not isinstance(raw_items, list):
                raise ValueError("items must be an array")
            batch_inputs: list[InvoiceBatchInput] = []
            for raw_item in raw_items:
                if not isinstance(raw_item, dict):
                    raise ValueError("batch item must be an object")
                raw_subjects = raw_item.get("subjects")
                if not isinstance(raw_subjects, list):
                    raise ValueError("batch item subjects must be an array")
                batch_inputs.append(
                    InvoiceBatchInput(
                        payload=dict(raw_item.get("payload") or {}),
                        subjects=tuple(
                            CaseSubjectInput(
                                business_object_id=UUID(str(value["businessObjectId"])),
                                business_object_version_id=UUID(
                                    str(value["businessObjectVersionId"])
                                ),
                                role=str(value["role"]),
                                subject_key=str(value["subjectKey"]),
                            )
                            for value in raw_subjects
                            if isinstance(value, dict)
                        ),
                        owner=(
                            str(raw_item["owner"])
                            if raw_item.get("owner") is not None
                            else None
                        ),
                    )
                )
            batch = await _invoice_assurance_operations.create_batch(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                inputs=tuple(batch_inputs),
                max_parallelism=int(arguments.get("maxParallelism", 3)),
                idempotency_key=str(arguments["idempotencyKey"]),
                actor=identity.subject_id,
                submitted_scopes=effective_scopes,
                auth_context_hash=identity.context_hash,
            )
            return _invoice_batch_snapshot(batch).model_dump(by_alias=True, mode="json")
        if name == "get_invoice_assurance_batch":
            batch = await _invoice_assurance_operations.get_batch(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                batch_id=UUID(str(arguments["batchId"])),
            )
            return _invoice_batch_snapshot(batch).model_dump(by_alias=True, mode="json")
        if name == "get_invoice_assurance_rule_trends":
            bucket = str(arguments.get("bucket", "day"))
            if bucket not in {"day", "week", "month"}:
                raise ValueError("invalid trend bucket")
            return await _invoice_assurance_operations.rule_trends(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                bucket=cast(Literal["day", "week", "month"], bucket),
            )
        if name == "list_documents":
            document_rows = await _documents.list_documents(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                search=(
                    str(arguments["search"])
                    if arguments.get("search") is not None
                    else None
                ),
                category=(
                    str(arguments["category"])
                    if arguments.get("category") is not None
                    else None
                ),
                status=(
                    str(arguments["status"])
                    if arguments.get("status") is not None
                    else None
                ),
            )
            return {
                "items": [
                    {
                        "documentId": str(document.id),
                        "name": document.name,
                        "category": document.category,
                        "tags": list(document.tags),
                        "status": document.status,
                        "currentVersion": document.current_version,
                        "updatedAt": document.updated_at.isoformat(),
                        "current": (
                            {
                                "documentVersionId": str(version.id),
                                "blobId": str(version.blob_id),
                                "version": version.version,
                                "filename": version.filename,
                                "mediaType": version.media_type,
                                "sizeBytes": version.size_bytes,
                                "sha256": version.sha256,
                            }
                            if version is not None
                            else None
                        ),
                    }
                    for document, version in document_rows
                ]
            }
        if name == "create_work_item":
            item, revision = await _workbench.create_work_item(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                work_item_type=str(arguments["workItemType"]),
                payload=dict(arguments["payload"]),
                owner=str(arguments["owner"]) if arguments.get("owner") is not None else None,
                idempotency_key=str(arguments["idempotencyKey"]),
                actor=identity.subject_id,
            )
            return {
                "workItemId": str(item.id),
                "workItemType": item.work_item_type,
                "schemaVersion": item.schema_version,
                "payload": item.payload,
                "status": item.status,
                "owner": item.owner,
                "revisionId": str(revision.id),
                "revision": revision.revision,
                "payloadHash": revision.payload_hash,
            }
        if name == "upsert_business_object":
            value, object_version, created = await _business_objects.upsert(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                object_type=str(arguments["objectType"]),
                canonical_key=str(arguments["canonicalKey"]),
                schema_ref=str(arguments["schemaRef"]),
                data=dict(arguments["data"]),
                provenance=dict(arguments.get("provenance", {})),
                actor=identity.subject_id,
            )
            return {
                "businessObjectId": str(value.id),
                "versionId": str(object_version.id),
                "version": object_version.version,
                "dataHash": object_version.data_hash,
                "created": created,
            }
        if name == "create_case":
            raw_subjects = arguments["subjects"]
            if not isinstance(raw_subjects, list):
                raise ValueError("subjects must be an array")
            subject_inputs = [
                CaseSubjectInput(
                    business_object_id=UUID(str(value["businessObjectId"])),
                    business_object_version_id=UUID(str(value["businessObjectVersionId"])),
                    role=str(value["role"]),
                    subject_key=str(value["subjectKey"]),
                )
                for value in raw_subjects
                if isinstance(value, dict)
            ]
            item, revision, subjects = await _cases.create(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                scenario_type=str(arguments["scenarioType"]),
                payload=dict(arguments["payload"]),
                subjects=subject_inputs,
                owner=(str(arguments["owner"]) if arguments.get("owner") else None),
                idempotency_key=str(arguments["idempotencyKey"]),
                actor=identity.subject_id,
            )
            return {
                "caseId": str(item.id),
                "caseRevisionId": str(revision.id),
                "scenarioType": item.work_item_type,
                "revision": revision.revision,
                "subjectCount": len(subjects),
            }
        if name == "assess_case":
            evaluation = await _cases.assess(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                case_id=UUID(str(arguments["caseId"])),
                idempotency_key=str(arguments["idempotencyKey"]),
                actor=identity.subject_id,
                submitted_scopes=effective_scopes,
                auth_context_hash=identity.context_hash,
            )
            return _evaluation_payload(evaluation)
        if name == "get_case_result":
            case_id = UUID(str(arguments["caseId"]))
            item, revision, subjects = await _cases.get(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                case_id=case_id,
            )
            from sqlalchemy import select
            from swarmcore_persistence.models import Evaluation

            latest_evaluation = await session.scalar(
                select(Evaluation)
                .where(
                    Evaluation.tenant_id == tenant_id,
                    Evaluation.project_id == project_id,
                    Evaluation.work_item_id == case_id,
                )
                .order_by(Evaluation.created_at.desc())
                .limit(1)
            )
            return {
                "caseId": str(item.id),
                "caseRevisionId": str(revision.id),
                "scenarioType": item.work_item_type,
                "subjectCount": len(subjects),
                "latestAssessment": (
                    _evaluation_payload(latest_evaluation)
                    if latest_evaluation is not None
                    else None
                ),
            }
        if name == "list_case_findings":
            findings = await _workbench.list_findings(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                work_item_id=UUID(str(arguments["caseId"])),
            )
            return {"items": [_finding_payload(finding) for finding in findings]}
        if name == "execute_work_item":
            evaluation = await _workbench.execute(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                work_item_id=UUID(str(arguments["workItemId"])),
                idempotency_key=str(arguments["idempotencyKey"]),
                actor=identity.subject_id,
                submitted_scopes=effective_scopes,
                auth_context_hash=identity.context_hash,
            )
            return _evaluation_payload(evaluation)
        if name == "get_evaluation":
            evaluation = await _workbench.get_evaluation(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                evaluation_id=UUID(str(arguments["evaluationId"])),
            )
            return _evaluation_payload(evaluation)
        if name == "list_findings":
            findings = await _workbench.list_findings(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                work_item_id=UUID(str(arguments["workItemId"])),
            )
            return {"items": [_finding_payload(finding) for finding in findings]}
        if name == "act_on_finding":
            finding = await _workbench.act_on_finding(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                finding_id=UUID(str(arguments["findingId"])),
                action=str(arguments["action"]),
                reason=(str(arguments["reason"]) if arguments.get("reason") is not None else None),
                assignee=(
                    str(arguments["assignee"]) if arguments.get("assignee") is not None else None
                ),
                expires_at=None,
                idempotency_key=str(arguments["idempotencyKey"]),
                actor=identity.subject_id,
            )
            return _finding_payload(finding)
        if name == "get_report":
            reports = await _workbench.list_reports(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                evaluation_id=UUID(str(arguments["evaluationId"])),
            )
            return {
                "items": [
                    {
                        "reportId": str(report.id),
                        "evaluationId": str(report.evaluation_id),
                        "format": report.format,
                        "templateVersion": report.template_version,
                        "resultSchemaVersion": report.result_schema_version,
                        "content": report.content,
                        "contentHash": report.content_hash,
                    }
                    for report in reports
                ]
            }
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


def _evaluation_payload(evaluation: Any) -> dict[str, Any]:
    return {
        "evaluationId": str(evaluation.id),
        "workItemId": str(evaluation.work_item_id),
        "workItemRevisionId": str(evaluation.work_item_revision_id),
        "runId": str(evaluation.run_id),
        "status": evaluation.status,
        "result": evaluation.result,
        "capabilityPackVersionId": str(evaluation.capability_pack_version_id),
        "ruleSetVersionId": (
            str(evaluation.rule_set_version_id)
            if evaluation.rule_set_version_id is not None
            else None
        ),
        "planHash": evaluation.plan_hash,
        "attachmentManifestHash": evaluation.attachment_manifest_hash,
        "registrySnapshot": evaluation.registry_snapshot,
    }


def _finding_payload(finding: Any) -> dict[str, Any]:
    return {
        "findingId": str(finding.id),
        "workItemId": str(finding.work_item_id),
        "evaluationId": str(finding.evaluation_id),
        "ruleKey": finding.rule_key,
        "code": finding.code,
        "category": finding.category,
        "severity": finding.severity,
        "status": finding.status,
        "title": finding.title,
        "detail": finding.detail,
        "evidence": finding.evidence,
    }
