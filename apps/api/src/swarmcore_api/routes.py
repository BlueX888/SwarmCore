from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated, Any
from uuid import NAMESPACE_URL, UUID, uuid5

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from jsonschema import Draft202012Validator
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_compiler import CompileError
from swarmcore_persistence import tenant_transaction
from swarmcore_persistence.models import (
    ApprovalRequest,
    ExternalInputRequest,
    Run,
    RunCommand,
    RunEvent,
    RunTask,
    Strategy,
    StrategyDraft,
    StrategyVersion,
)

from .dependencies import RequestScope, db_session, request_scope, require_idempotency_key
from .schemas import (
    ApprovalListResponse,
    ApprovalSnapshot,
    CommandHandle,
    CompileRequest,
    CompileResponse,
    CreateRunRequest,
    CreateStrategyRequest,
    DraftSnapshot,
    ExternalInputListResponse,
    ExternalInputSnapshot,
    HumanResponseRequest,
    PublishRequest,
    RunHandle,
    RunListResponse,
    RunSnapshot,
    StrategyDetail,
    StrategyHandle,
    StrategyListResponse,
    StrategySummary,
    StrategyVersionDetail,
    StrategyVersionHandle,
    StrategyVersionListResponse,
    StrategyVersionSummary,
    TaskSnapshot,
    UpdateDraftRequest,
)
from .services import RunService, StrategyService

router = APIRouter(prefix="/v1")
strategies = StrategyService()
runs = RunService()

Scope = Annotated[RequestScope, Depends(request_scope)]
Session = Annotated[AsyncSession, Depends(db_session)]


@router.post(
    "/projects/{project_id}/strategies/compile",
    response_model=CompileResponse,
)
async def compile_strategy(body: CompileRequest, scope: Scope) -> CompileResponse:
    del scope
    try:
        _, plan = strategies.compile(
            body.spec,
            registry_snapshot=body.registry_snapshot,
            policy_revision=body.policy_revision,
        )
        return CompileResponse(valid=True, plan=plan.model_dump(mode="json", by_alias=True))
    except CompileError as exc:
        return CompileResponse(
            valid=False,
            diagnostics=[item.model_dump(mode="json") for item in exc.diagnostics],
        )
    except ValidationError as exc:
        return CompileResponse(
            valid=False,
            diagnostics=[
                {
                    "severity": "error",
                    "code": "STRUCTURAL_VALIDATION_ERROR",
                    "path": "$." + ".".join(str(part) for part in item["loc"]),
                    "message": item["msg"],
                }
                for item in exc.errors(include_url=False)
            ],
        )


@router.post(
    "/projects/{project_id}/strategies",
    response_model=StrategyHandle,
    status_code=201,
)
async def create_strategy(
    body: CreateStrategyRequest,
    scope: Scope,
    session: Session,
    actor: Annotated[str, Header(alias="X-Actor-ID")] = "local-user",
) -> StrategyHandle:
    strategy, draft = await strategies.create_draft(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        name=body.name,
        raw_spec=body.spec,
        actor=actor,
    )
    return StrategyHandle(strategyId=strategy.id, draftId=draft.id, revision=draft.revision)


@router.get("/projects/{project_id}/strategies", response_model=StrategyListResponse)
async def list_strategies(
    scope: Scope,
    session: Session,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> StrategyListResponse:
    query = (
        select(Strategy)
        .where(Strategy.tenant_id == scope.tenant_id, Strategy.project_id == scope.project_id)
        .order_by(Strategy.updated_at.desc(), Strategy.id)
        .offset(offset)
        .limit(limit)
    )
    items = list(await session.scalars(query))
    summaries = [await _strategy_summary(session, item) for item in items]
    total = await session.scalar(
        select(func.count()).select_from(Strategy).where(
            Strategy.tenant_id == scope.tenant_id,
            Strategy.project_id == scope.project_id,
        )
    )
    return StrategyListResponse(items=summaries, total=total or 0)


@router.get("/projects/{project_id}/strategies/{strategy_id}", response_model=StrategyDetail)
async def get_strategy(strategy_id: UUID, scope: Scope, session: Session) -> StrategyDetail:
    strategy = await _get_scoped_strategy(session, scope, strategy_id)
    summary = await _strategy_summary(session, strategy)
    return StrategyDetail(**summary.model_dump(), projectId=strategy.project_id)


@router.get(
    "/projects/{project_id}/strategies/{strategy_id}/drafts/{draft_id}",
    response_model=DraftSnapshot,
)
async def get_strategy_draft(
    strategy_id: UUID,
    draft_id: UUID,
    scope: Scope,
    session: Session,
    response: Response,
) -> DraftSnapshot:
    await _get_scoped_strategy(session, scope, strategy_id)
    draft = await session.scalar(
        select(StrategyDraft).where(
            StrategyDraft.id == draft_id,
            StrategyDraft.strategy_id == strategy_id,
            StrategyDraft.tenant_id == scope.tenant_id,
        )
    )
    if draft is None:
        raise HTTPException(status_code=404, detail="draft not found")
    response.headers["ETag"] = f'"{draft.revision}"'
    return _draft_snapshot(draft)


@router.get(
    "/projects/{project_id}/strategies/{strategy_id}/versions",
    response_model=StrategyVersionListResponse,
)
async def list_strategy_versions(
    strategy_id: UUID, scope: Scope, session: Session
) -> StrategyVersionListResponse:
    await _get_scoped_strategy(session, scope, strategy_id)
    versions = list(
        await session.scalars(
            select(StrategyVersion)
            .where(
                StrategyVersion.strategy_id == strategy_id,
                StrategyVersion.tenant_id == scope.tenant_id,
            )
            .order_by(StrategyVersion.version.desc())
        )
    )
    return StrategyVersionListResponse(
        items=[_version_summary(item) for item in versions], total=len(versions)
    )


@router.get(
    "/projects/{project_id}/strategies/{strategy_id}/versions/{version_id}",
    response_model=StrategyVersionDetail,
)
async def get_strategy_version(
    strategy_id: UUID, version_id: UUID, scope: Scope, session: Session
) -> StrategyVersionDetail:
    await _get_scoped_strategy(session, scope, strategy_id)
    version = await session.scalar(
        select(StrategyVersion).where(
            StrategyVersion.id == version_id,
            StrategyVersion.strategy_id == strategy_id,
            StrategyVersion.tenant_id == scope.tenant_id,
        )
    )
    if version is None:
        raise HTTPException(status_code=404, detail="strategy version not found")
    return StrategyVersionDetail(
        **_version_summary(version).model_dump(),
        spec=version.raw_spec,
        normalizedSpec=version.normalized_spec,
        plan=version.plan,
    )


@router.put(
    "/projects/{project_id}/strategies/{strategy_id}/drafts/{draft_id}",
    response_model=StrategyHandle,
)
async def update_strategy_draft(
    strategy_id: UUID,
    draft_id: UUID,
    body: UpdateDraftRequest,
    scope: Scope,
    session: Session,
    response: Response,
    if_match: Annotated[str, Header(alias="If-Match")],
    actor: Annotated[str, Header(alias="X-Actor-ID")] = "local-user",
) -> StrategyHandle:
    try:
        expected_revision = int(if_match.strip('W/"'))
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail="If-Match must contain the draft revision"
        ) from exc
    draft = await strategies.update_draft(
        session,
        tenant_id=scope.tenant_id,
        strategy_id=strategy_id,
        draft_id=draft_id,
        expected_revision=expected_revision,
        raw_spec=body.spec,
        actor=actor,
    )
    response.headers["ETag"] = f'"{draft.revision}"'
    return StrategyHandle(strategyId=strategy_id, draftId=draft.id, revision=draft.revision)


@router.post(
    "/projects/{project_id}/strategies/{strategy_id}/publish",
    response_model=StrategyVersionHandle,
)
async def publish_strategy(
    strategy_id: UUID,
    body: PublishRequest,
    scope: Scope,
    session: Session,
) -> StrategyVersionHandle:
    version = await strategies.publish(
        session,
        tenant_id=scope.tenant_id,
        strategy_id=strategy_id,
        draft_id=body.draft_id,
        registry_snapshot=body.registry_snapshot,
        policy_revision=body.policy_revision,
    )
    return StrategyVersionHandle(
        strategyId=strategy_id,
        strategyVersionId=version.id,
        version=version.version,
        planHash=version.plan_hash,
    )


@router.post("/projects/{project_id}/runs", response_model=RunHandle, status_code=202)
async def create_run(
    body: CreateRunRequest,
    scope: Scope,
    session: Session,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
) -> RunHandle:
    run, command = await runs.create(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        strategy_version_id=body.strategy_version_id,
        input_data=body.input,
        idempotency_key=idempotency_key,
    )
    return RunHandle(
        runId=run.id,
        status=run.status,
        commandId=command.id,
        commandStatus=command.status,
    )


@router.get("/projects/{project_id}/runs/{run_id}", response_model=RunSnapshot)
async def get_run(run_id: UUID, scope: Scope, session: Session) -> RunSnapshot:
    run = await session.scalar(
        select(Run).where(Run.id == run_id, Run.tenant_id == scope.tenant_id)
    )
    if run is None or run.project_id != scope.project_id:
        raise HTTPException(status_code=404, detail="run not found")
    tasks = list(
        await session.scalars(
            select(RunTask).where(RunTask.run_id == run_id).order_by(RunTask.task_instance_key)
        )
    )
    task_events = list(
        await session.scalars(
            select(RunEvent).where(
                RunEvent.run_id == run_id,
                RunEvent.task_id.is_not(None),
                RunEvent.type.in_(("task.failed", "task.completed")),
            )
        )
    )
    errors = {
        item.task_id: item.payload.get("error")
        for item in task_events
        if item.type == "task.failed" and isinstance(item.payload.get("error"), dict)
    }
    outputs = {
        item.task_id: item.payload.get("output")
        for item in task_events
        if item.type == "task.completed" and isinstance(item.payload.get("output"), dict)
    }
    return _run_snapshot(run, tasks, errors=errors, outputs=outputs)


@router.get("/projects/{project_id}/runs", response_model=RunListResponse)
async def list_runs(
    scope: Scope,
    session: Session,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> RunListResponse:
    query = (
        select(Run)
        .where(Run.tenant_id == scope.tenant_id, Run.project_id == scope.project_id)
        .order_by(Run.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = list(await session.scalars(query))
    total = (
        await session.scalar(
            select(func.count()).select_from(Run).where(
                Run.tenant_id == scope.tenant_id,
                Run.project_id == scope.project_id,
            )
        )
        or 0
    )
    snapshots: list[RunSnapshot] = []
    for run in items:
        tasks = list(
            await session.scalars(
                select(RunTask).where(RunTask.run_id == run.id).order_by(RunTask.task_instance_key)
            )
        )
        snapshots.append(_run_snapshot(run, tasks))
    return RunListResponse(items=snapshots, total=total)


@router.post(
    "/projects/{project_id}/runs/{run_id}:cancel",
    response_model=CommandHandle,
    status_code=202,
)
async def cancel_run(
    run_id: UUID,
    scope: Scope,
    session: Session,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
    actor: Annotated[str, Header(alias="X-Actor-ID")] = "local-user",
) -> CommandHandle:
    run = await _get_scoped_run(session, scope, run_id)
    if run.status in _TERMINAL_RUN_STATUSES:
        raise HTTPException(status_code=409, detail="run is already terminal")
    return await _append_command(
        session, scope, run_id, "cancel", idempotency_key, {}, actor=actor
    )


@router.post(
    "/projects/{project_id}/runs/{run_id}:pause",
    response_model=CommandHandle,
    status_code=202,
)
async def pause_run(
    run_id: UUID,
    scope: Scope,
    session: Session,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
    actor: Annotated[str, Header(alias="X-Actor-ID")] = "local-user",
) -> CommandHandle:
    run = await _get_scoped_run(session, scope, run_id)
    if run.status not in {"QUEUED", "RUNNING", "WAITING_APPROVAL", "WAITING_INPUT"}:
        raise HTTPException(status_code=409, detail=f"run cannot be paused from {run.status}")
    return await _append_command(
        session, scope, run_id, "pause", idempotency_key, {}, actor=actor
    )


@router.post(
    "/projects/{project_id}/runs/{run_id}:resume",
    response_model=CommandHandle,
    status_code=202,
)
async def resume_run(
    run_id: UUID,
    scope: Scope,
    session: Session,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
    actor: Annotated[str, Header(alias="X-Actor-ID")] = "local-user",
) -> CommandHandle:
    run = await _get_scoped_run(session, scope, run_id)
    if run.status not in {"PAUSING", "PAUSED"}:
        raise HTTPException(status_code=409, detail=f"run cannot be resumed from {run.status}")
    return await _append_command(
        session, scope, run_id, "resume", idempotency_key, {}, actor=actor
    )


@router.get("/projects/{project_id}/approvals", response_model=ApprovalListResponse)
async def list_approvals(
    scope: Scope,
    session: Session,
    run_id: Annotated[UUID | None, Query(alias="runId")] = None,
) -> ApprovalListResponse:
    query = select(ApprovalRequest).where(
        ApprovalRequest.tenant_id == scope.tenant_id,
        ApprovalRequest.project_id == scope.project_id,
        ApprovalRequest.status == "PENDING",
    )
    if run_id is not None:
        query = query.where(ApprovalRequest.run_id == run_id)
    items = list(await session.scalars(query.order_by(ApprovalRequest.created_at)))
    return ApprovalListResponse(
        items=[_approval_snapshot(item) for item in items], total=len(items)
    )


@router.post(
    "/projects/{project_id}/approvals/{approval_id}:approve",
    response_model=CommandHandle,
    status_code=202,
)
async def approve(
    approval_id: UUID,
    body: HumanResponseRequest,
    scope: Scope,
    session: Session,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
    actor: Annotated[str, Header(alias="X-Actor-ID")] = "local-user",
) -> CommandHandle:
    request = await _get_approval(session, scope, approval_id)
    Draft202012Validator(request.input_schema).validate(body.value)
    _reject_secret_material(body.value)
    return await _handle_approval(
        session, scope, request, "approve", idempotency_key, body.value, actor
    )


@router.post(
    "/projects/{project_id}/approvals/{approval_id}:reject",
    response_model=CommandHandle,
    status_code=202,
)
async def reject(
    approval_id: UUID,
    body: HumanResponseRequest,
    scope: Scope,
    session: Session,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
    actor: Annotated[str, Header(alias="X-Actor-ID")] = "local-user",
) -> CommandHandle:
    request = await _get_approval(session, scope, approval_id)
    return await _handle_approval(
        session, scope, request, "reject", idempotency_key, body.value, actor
    )


@router.get("/projects/{project_id}/inputs", response_model=ExternalInputListResponse)
async def list_inputs(
    scope: Scope,
    session: Session,
    run_id: Annotated[UUID | None, Query(alias="runId")] = None,
) -> ExternalInputListResponse:
    query = select(ExternalInputRequest).where(
        ExternalInputRequest.tenant_id == scope.tenant_id,
        ExternalInputRequest.project_id == scope.project_id,
        ExternalInputRequest.status == "PENDING",
    )
    if run_id is not None:
        query = query.where(ExternalInputRequest.run_id == run_id)
    items = list(await session.scalars(query.order_by(ExternalInputRequest.created_at)))
    return ExternalInputListResponse(
        items=[_input_snapshot(item) for item in items], total=len(items)
    )


@router.post(
    "/projects/{project_id}/inputs/{input_request_id}:provide",
    response_model=CommandHandle,
    status_code=202,
)
async def provide_input(
    input_request_id: UUID,
    body: HumanResponseRequest,
    scope: Scope,
    session: Session,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
    actor: Annotated[str, Header(alias="X-Actor-ID")] = "local-user",
) -> CommandHandle:
    request = await _get_input(session, scope, input_request_id)
    if request.status != "PENDING":
        raise HTTPException(status_code=410, detail="input request was already handled")
    Draft202012Validator(request.input_schema).validate(body.value)
    _reject_secret_material(body.value)
    handle = await _append_command(
        session,
        scope,
        request.run_id,
        "provide_input",
        idempotency_key,
        {
            "requestId": str(request.id),
            "nodeKey": request.node_key,
            "value": body.value,
            "actor": actor,
        },
        actor=actor,
    )
    if request.handler_command_id not in {None, handle.command_id}:
        raise HTTPException(status_code=409, detail="input request already has a pending command")
    request.handler_command_id = handle.command_id
    request.handled_by = actor
    return handle


@router.post(
    "/projects/{project_id}/runs/{run_id}/tasks/{task_id}:retry",
    response_model=CommandHandle,
    status_code=202,
)
async def retry_task(
    run_id: UUID,
    task_id: UUID,
    scope: Scope,
    session: Session,
    idempotency_key: Annotated[str, Depends(require_idempotency_key)],
    actor: Annotated[str, Header(alias="X-Actor-ID")] = "local-user",
) -> CommandHandle:
    run = await _get_scoped_run(session, scope, run_id)
    task = await session.scalar(
        select(RunTask).where(
            RunTask.id == task_id,
            RunTask.run_id == run.id,
            RunTask.tenant_id == scope.tenant_id,
        )
    )
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    if task.status != "FAILED" or run.status != "FAILED":
        raise HTTPException(status_code=409, detail="task is not retryable")
    handle = await _append_command(
        session,
        scope,
        run_id,
        "retry_task",
        idempotency_key,
        {"taskId": str(task.id), "nodeKey": task.node_key, "generation": task.retry_generation + 1},
        actor=actor,
    )
    task.last_retry_command_id = handle.command_id
    return handle


@router.get("/projects/{project_id}/commands/{command_id}", response_model=CommandHandle)
async def get_command(command_id: UUID, scope: Scope, session: Session) -> CommandHandle:
    command = await session.scalar(
        select(RunCommand)
        .join(Run, Run.id == RunCommand.run_id)
        .where(
            RunCommand.id == command_id,
            RunCommand.tenant_id == scope.tenant_id,
            Run.project_id == scope.project_id,
        )
    )
    if command is None:
        raise HTTPException(status_code=404, detail="command not found")
    return CommandHandle(
        commandId=command.id,
        requestId=command.request_id,
        commandSeq=command.command_seq,
        status=command.status,
        result=command.result,
        error=command.error,
        createdAt=command.created_at,
        appliedAt=command.applied_at,
        rejectedAt=command.rejected_at,
    )


@router.get("/projects/{project_id}/runs/{run_id}/event-history")
async def event_history(
    run_id: UUID,
    scope: Scope,
    session: Session,
    after: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> dict[str, Any]:
    run = await _get_scoped_run(session, scope, run_id)
    _check_cursor(run, after)
    events = list(
        await session.scalars(
            select(RunEvent)
            .where(RunEvent.run_id == run_id, RunEvent.event_seq > after)
            .order_by(RunEvent.event_seq)
            .limit(limit)
        )
    )
    return {
        "items": [_event_envelope(item) for item in events],
        "nextAfter": events[-1].event_seq if events else after,
    }


@router.get("/projects/{project_id}/runs/{run_id}/events")
async def stream_events(
    request: Request,
    run_id: UUID,
    scope: Scope,
    session: Session,
    after: Annotated[int | None, Query(ge=0)] = None,
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> StreamingResponse:
    cursor = after if after is not None else int(last_event_id or 0)
    run = await _get_scoped_run(session, scope, run_id)
    _check_cursor(run, cursor)
    high_water = (
        await session.scalar(select(func.max(RunEvent.event_seq)).where(RunEvent.run_id == run_id))
        or 0
    )
    database = request.app.state.database
    poll_interval = request.app.state.settings.event_poll_interval_seconds

    async def generate() -> AsyncIterator[str]:
        current = cursor
        while not await request.is_disconnected():
            async with tenant_transaction(
                database.sessions,
                tenant_id=scope.tenant_id,
                project_id=scope.project_id,
            ) as event_session:
                upper_bound = high_water if current < high_water else None
                query = select(RunEvent).where(
                    RunEvent.run_id == run_id,
                    RunEvent.event_seq > current,
                )
                if upper_bound is not None:
                    query = query.where(RunEvent.event_seq <= upper_bound)
                items = list(
                    await event_session.scalars(query.order_by(RunEvent.event_seq).limit(100))
                )
            if items:
                for item in items:
                    current = item.event_seq
                    yield format_sse(item)
                continue
            yield ": heartbeat\n\n"
            await asyncio.sleep(poll_interval)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _get_scoped_run(session: AsyncSession, scope: RequestScope, run_id: UUID) -> Run:
    run = await session.scalar(
        select(Run).where(Run.id == run_id, Run.tenant_id == scope.tenant_id)
    )
    if run is None or run.project_id != scope.project_id:
        raise HTTPException(status_code=404, detail="run not found")
    return run


_TERMINAL_RUN_STATUSES = {"REJECTED", "CANCELLED", "SUCCEEDED", "TIMED_OUT"}


async def _append_command(
    session: AsyncSession,
    scope: RequestScope,
    run_id: UUID,
    command_type: str,
    idempotency_key: str,
    payload: dict[str, Any],
    *,
    actor: str,
) -> CommandHandle:
    request_id = uuid5(
        NAMESPACE_URL,
        f"{scope.tenant_id}:{run_id}:{command_type}:{idempotency_key}",
    )
    command = await runs.commands.append(
        session,
        tenant_id=scope.tenant_id,
        run_id=run_id,
        command_type=command_type,
        request_id=request_id,
        payload=payload,
        actor=actor,
    )
    return _command_handle(command)


def _command_handle(command: RunCommand) -> CommandHandle:
    return CommandHandle(
        commandId=command.id,
        requestId=command.request_id,
        commandSeq=command.command_seq,
        status=command.status,
        result=command.result,
        error=command.error,
        createdAt=command.created_at,
        appliedAt=command.applied_at,
        rejectedAt=command.rejected_at,
    )


async def _get_approval(
    session: AsyncSession, scope: RequestScope, approval_id: UUID
) -> ApprovalRequest:
    request = await session.scalar(
        select(ApprovalRequest).where(
            ApprovalRequest.id == approval_id,
            ApprovalRequest.tenant_id == scope.tenant_id,
            ApprovalRequest.project_id == scope.project_id,
        )
    )
    if request is None:
        raise HTTPException(status_code=404, detail="approval request not found")
    return request


async def _get_input(
    session: AsyncSession, scope: RequestScope, input_request_id: UUID
) -> ExternalInputRequest:
    request = await session.scalar(
        select(ExternalInputRequest).where(
            ExternalInputRequest.id == input_request_id,
            ExternalInputRequest.tenant_id == scope.tenant_id,
            ExternalInputRequest.project_id == scope.project_id,
        )
    )
    if request is None:
        raise HTTPException(status_code=404, detail="external input request not found")
    return request


async def _handle_approval(
    session: AsyncSession,
    scope: RequestScope,
    request: ApprovalRequest,
    command_type: str,
    idempotency_key: str,
    value: dict[str, Any],
    actor: str,
) -> CommandHandle:
    if request.status != "PENDING":
        raise HTTPException(status_code=410, detail="approval request was already handled")
    handle = await _append_command(
        session,
        scope,
        request.run_id,
        command_type,
        idempotency_key,
        {
            "requestId": str(request.id),
            "nodeKey": request.node_key,
            "value": value,
            "actor": actor,
        },
        actor=actor,
    )
    if request.handler_command_id not in {None, handle.command_id}:
        raise HTTPException(
            status_code=409, detail="approval request already has a pending command"
        )
    request.handler_command_id = handle.command_id
    request.handled_by = actor
    return handle


def _approval_snapshot(request: ApprovalRequest) -> ApprovalSnapshot:
    return ApprovalSnapshot(
        approvalId=request.id,
        runId=request.run_id,
        nodeKey=request.node_key,
        prompt=request.prompt,
        inputSchema=request.input_schema,
        status=request.status,
        allowedActions=["approve", "reject"] if request.status == "PENDING" else [],
        requestedBy=request.requested_by,
        handledBy=request.handled_by,
        createdAt=request.created_at,
        handledAt=request.handled_at,
    )


def _input_snapshot(request: ExternalInputRequest) -> ExternalInputSnapshot:
    return ExternalInputSnapshot(
        inputRequestId=request.id,
        runId=request.run_id,
        nodeKey=request.node_key,
        prompt=request.prompt,
        inputSchema=request.input_schema,
        status=request.status,
        allowedActions=["provide_input"] if request.status == "PENDING" else [],
        requestedBy=request.requested_by,
        handledBy=request.handled_by,
        createdAt=request.created_at,
        handledAt=request.handled_at,
    )


def _reject_secret_material(value: Any, path: str = "$") -> None:
    secret_names = {"secret", "password", "token", "api_key", "apikey", "private_key"}
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in secret_names:
                raise HTTPException(
                    status_code=422,
                    detail=f"plaintext secret material is not accepted at {path}.{key}",
                )
            _reject_secret_material(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_secret_material(item, f"{path}[{index}]")


def _check_cursor(run: Run, after: int) -> None:
    if after and after < run.earliest_available_seq - 1:
        raise HTTPException(status_code=410, detail="CURSOR_EXPIRED")


def _run_snapshot(
    run: Run,
    tasks: list[RunTask] | None = None,
    *,
    errors: dict[UUID | None, Any] | None = None,
    outputs: dict[UUID | None, Any] | None = None,
) -> RunSnapshot:
    task_items = tasks or []
    task_counts: dict[str, int] = {}
    for task in task_items:
        task_counts[task.status] = task_counts.get(task.status, 0) + 1
    actions: list[str] = []
    if run.status in {"QUEUED", "RUNNING", "WAITING_APPROVAL", "WAITING_INPUT"}:
        actions.append("pause")
    if run.status in {"PAUSING", "PAUSED"}:
        actions.append("resume")
    if run.status not in _TERMINAL_RUN_STATUSES | {"FAILED"}:
        actions.append("cancel")
    if run.status == "FAILED" and any(task.status == "FAILED" for task in task_items):
        actions.append("retry_task")
    return RunSnapshot(
        runId=run.id,
        status=run.status,
        input=run.input,
        output=run.output,
        outputRef=run.output_ref,
        snapshotSeq=run.next_event_seq - 1,
        earliestAvailableSeq=run.earliest_available_seq,
        planHash=run.plan_hash,
        usage=run.usage,
        taskCounts=task_counts,
        allowedActions=actions,
        startedAt=run.started_at,
        completedAt=run.completed_at,
        tasks=[
            TaskSnapshot(
                taskId=task.id,
                nodeKey=task.node_key,
                nodeType=task.node_type,
                status=task.status,
                dependencies=task.dependencies,
                error=(errors or {}).get(task.id),
                output=(outputs or {}).get(task.id),
                retryGeneration=task.retry_generation,
                allowedActions=["retry_task"]
                if run.status == "FAILED" and task.status == "FAILED"
                else [],
            )
            for task in task_items
        ],
    )


def _event_envelope(event: RunEvent) -> dict[str, Any]:
    return {
        "id": str(event.id),
        "seq": event.event_seq,
        "type": event.type,
        "schemaVersion": event.schema_version,
        "tenantId": str(event.tenant_id),
        "projectId": str(event.project_id),
        "runId": str(event.run_id),
        "taskId": str(event.task_id) if event.task_id else None,
        "attemptId": str(event.attempt_id) if event.attempt_id else None,
        "occurredAt": event.occurred_at.isoformat(),
        "traceId": event.trace_id,
        "causationId": str(event.causation_id) if event.causation_id else None,
        "correlationId": str(event.correlation_id) if event.correlation_id else None,
        "redacted": event.redacted,
        "data": event.payload,
    }


async def _get_scoped_strategy(
    session: AsyncSession, scope: RequestScope, strategy_id: UUID
) -> Strategy:
    strategy = await session.scalar(
        select(Strategy).where(
            Strategy.id == strategy_id,
            Strategy.tenant_id == scope.tenant_id,
            Strategy.project_id == scope.project_id,
        )
    )
    if strategy is None:
        raise HTTPException(status_code=404, detail="strategy not found")
    return strategy


async def _strategy_summary(session: AsyncSession, strategy: Strategy) -> StrategySummary:
    draft = await session.scalar(
        select(StrategyDraft)
        .where(
            StrategyDraft.strategy_id == strategy.id,
            StrategyDraft.tenant_id == strategy.tenant_id,
        )
        .order_by(StrategyDraft.updated_at.desc())
        .limit(1)
    )
    latest_version = await session.scalar(
        select(func.max(StrategyVersion.version)).where(
            StrategyVersion.strategy_id == strategy.id,
            StrategyVersion.tenant_id == strategy.tenant_id,
        )
    )
    return StrategySummary(
        strategyId=strategy.id,
        name=strategy.name,
        lifecycle=strategy.lifecycle,
        createdAt=strategy.created_at,
        updatedAt=strategy.updated_at,
        draftId=draft.id if draft else None,
        draftRevision=draft.revision if draft else None,
        latestVersion=latest_version,
    )


def _draft_snapshot(draft: StrategyDraft) -> DraftSnapshot:
    return DraftSnapshot(
        draftId=draft.id,
        strategyId=draft.strategy_id,
        revision=draft.revision,
        spec=draft.raw_spec,
        diagnostics=draft.diagnostics,
        updatedBy=draft.updated_by,
        updatedAt=draft.updated_at,
    )


def _version_summary(version: StrategyVersion) -> StrategyVersionSummary:
    return StrategyVersionSummary(
        strategyVersionId=version.id,
        strategyId=version.strategy_id,
        version=version.version,
        lifecycle=version.lifecycle,
        planHash=version.plan_hash,
        schemaVersion=version.schema_version,
        runtimeVersion=version.runtime_version,
        createdAt=version.created_at,
    )


def format_sse(event: RunEvent) -> str:
    data = json.dumps(_event_envelope(event), ensure_ascii=False, separators=(",", ":"))
    return f"id: {event.event_seq}\nevent: {event.type}\ndata: {data}\n\n"
