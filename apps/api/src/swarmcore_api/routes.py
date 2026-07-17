from __future__ import annotations

import asyncio
import hashlib
import json
import secrets
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any, Literal, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest
from urllib.request import urlopen
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from jsonschema import Draft202012Validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_application import (
    CapabilityCatalog,
    CapabilityCatalogService,
    CommandHandle,
    CompilationService,
    ConfigurationKind,
    ProjectConfigurationService,
    RunCommandService,
    RunQueryService,
    RunResult,
    RunResultService,
    RunService,
    StrategyService,
    render_run_snapshot,
)
from swarmcore_capability_contract_integrity import MANIFEST
from swarmcore_governance import (
    ArtifactCapabilityIssuer,
    WorkloadTls,
    validate_secret_ref,
    validate_webhook_target,
)
from swarmcore_persistence import AuditRepository, tenant_transaction
from swarmcore_persistence.models import (
    ApprovalRequest,
    Artifact,
    ArtifactDownloadGrant,
    AuditLog,
    ExternalInputRequest,
    ProjectConfiguration,
    Run,
    RunEvent,
    RunTask,
    Strategy,
    StrategyDraft,
    StrategyVersion,
    WebhookEndpoint,
)

from .dependencies import (
    RequestScope,
    authorize_rest,
    db_session,
    request_scope,
    require_idempotency_key,
)
from .schemas import (
    ApprovalListResponse,
    ApprovalSnapshot,
    ArtifactDownloadGrantResponse,
    ArtifactListResponse,
    ArtifactSnapshot,
    AuditListResponse,
    AuditSnapshot,
    CompileRequest,
    CompileResponse,
    CreateProjectConfigurationRequest,
    CreateRunRequest,
    CreateStrategyRequest,
    CreateWebhookRequest,
    DraftSnapshot,
    EditorState,
    ExternalInputListResponse,
    ExternalInputSnapshot,
    HumanResponseRequest,
    ProjectConfigurationListResponse,
    ProjectConfigurationSnapshot,
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
    UpdateDraftRequest,
    WebhookListResponse,
    WebhookSnapshot,
)

router = APIRouter(prefix="/v1", dependencies=[Depends(authorize_rest)])
strategies = StrategyService()
runs = RunService()
commands = RunCommandService()
run_queries = RunQueryService()
run_results = RunResultService()
capabilities = CapabilityCatalogService((MANIFEST,))
project_configurations = ProjectConfigurationService()
compilation = CompilationService(strategies)

Scope = Annotated[RequestScope, Depends(request_scope)]
Session = Annotated[AsyncSession, Depends(db_session)]


@router.get("/projects/{project_id}/capabilities", response_model=CapabilityCatalog)
async def get_capabilities(scope: Scope) -> CapabilityCatalog:
    del scope
    return capabilities.get()


@router.get(
    "/projects/{project_id}/configurations/{configuration_kind}",
    response_model=ProjectConfigurationListResponse,
)
async def list_project_configurations(
    configuration_kind: ConfigurationKind,
    scope: Scope,
    session: Session,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProjectConfigurationListResponse:
    items, total = await project_configurations.list(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        kind=configuration_kind,
        limit=limit,
        offset=offset,
    )
    return ProjectConfigurationListResponse(
        items=[_project_configuration_snapshot(item) for item in items],
        total=total,
    )


@router.post(
    "/projects/{project_id}/configurations/{configuration_kind}",
    response_model=ProjectConfigurationSnapshot,
    status_code=201,
)
async def create_project_configuration(
    configuration_kind: ConfigurationKind,
    body: CreateProjectConfigurationRequest,
    scope: Scope,
    session: Session,
) -> ProjectConfigurationSnapshot:
    saved = await project_configurations.create(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        kind=configuration_kind,
        name=body.name,
        source_ref=body.source_ref,
        configuration=body.configuration,
        actor=scope.actor_id,
    )
    return _project_configuration_snapshot(saved)


@router.put(
    "/projects/{project_id}/configurations/{configuration_kind}/{configuration_id}",
    response_model=ProjectConfigurationSnapshot,
)
async def update_project_configuration(
    configuration_kind: ConfigurationKind,
    configuration_id: UUID,
    body: CreateProjectConfigurationRequest,
    scope: Scope,
    session: Session,
) -> ProjectConfigurationSnapshot:
    saved = await project_configurations.update(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        kind=configuration_kind,
        configuration_id=configuration_id,
        name=body.name,
        source_ref=body.source_ref,
        configuration=body.configuration,
        actor=scope.actor_id,
    )
    return _project_configuration_snapshot(saved)


@router.delete(
    "/projects/{project_id}/configurations/{configuration_kind}/{configuration_id}",
    status_code=204,
)
async def delete_project_configuration(
    configuration_kind: ConfigurationKind,
    configuration_id: UUID,
    scope: Scope,
    session: Session,
) -> Response:
    await project_configurations.delete(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        kind=configuration_kind,
        configuration_id=configuration_id,
        actor=scope.actor_id,
    )
    return Response(status_code=204)


@router.post(
    "/projects/{project_id}/strategies/compile",
    response_model=CompileResponse,
)
async def compile_strategy(body: CompileRequest, scope: Scope) -> CompileResponse:
    del scope
    result = compilation.compile(
        body.spec,
        registry_snapshot=body.registry_snapshot,
        policy_revision=body.policy_revision,
    )
    return CompileResponse(
        valid=result.valid,
        plan=result.plan,
        diagnostics=result.diagnostics,
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
) -> StrategyHandle:
    strategy, draft = await strategies.create_draft(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        name=body.name,
        raw_spec=body.spec,
        editor_state=body.editor_state.model_dump(mode="json"),
        actor=scope.actor_id,
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
        select(func.count())
        .select_from(Strategy)
        .where(
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
    response_model=DraftSnapshot,
)
async def update_strategy_draft(
    strategy_id: UUID,
    draft_id: UUID,
    body: UpdateDraftRequest,
    scope: Scope,
    session: Session,
    response: Response,
    if_match: Annotated[str, Header(alias="If-Match")],
) -> DraftSnapshot:
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
        editor_state=(
            body.editor_state.model_dump(mode="json") if body.editor_state is not None else None
        ),
        actor=scope.actor_id,
    )
    response.headers["ETag"] = f'"{draft.revision}"'
    return _draft_snapshot(draft)


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
        actor=scope.actor_id,
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
    if body.spec is not None:
        run, command = await runs.create_inline(
            session,
            tenant_id=scope.tenant_id,
            project_id=scope.project_id,
            raw_spec=body.spec,
            input_data=body.input,
            idempotency_key=idempotency_key,
            initiated_by=scope.actor_id,
            submitted_scopes=scope.scopes,
            auth_context_hash=scope.auth_context_hash,
        )
    else:
        assert body.strategy_version_id is not None
        run, command = await runs.create(
            session,
            tenant_id=scope.tenant_id,
            project_id=scope.project_id,
            strategy_version_id=body.strategy_version_id,
            input_data=body.input,
            idempotency_key=idempotency_key,
            initiated_by=scope.actor_id,
            submitted_scopes=scope.scopes,
            auth_context_hash=scope.auth_context_hash,
        )
    return RunHandle(
        runId=run.id,
        status=run.status,
        commandId=command.id,
        commandStatus=command.status,
        planHash=run.plan_hash,
    )


@router.get("/projects/{project_id}/runs/{run_id}", response_model=RunSnapshot)
async def get_run(run_id: UUID, scope: Scope, session: Session) -> RunSnapshot:
    try:
        snapshot = await run_queries.get_snapshot(
            session,
            tenant_id=scope.tenant_id,
            project_id=scope.project_id,
            run_id=run_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RunSnapshot.model_validate(snapshot)


@router.get("/projects/{project_id}/runs/{run_id}/result", response_model=RunResult)
async def get_run_result(run_id: UUID, scope: Scope, session: Session) -> RunResult:
    return await run_results.get(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        run_id=run_id,
    )


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
            select(func.count())
            .select_from(Run)
            .where(
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
        snapshots.append(RunSnapshot.model_validate(render_run_snapshot(run, tasks)))
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
) -> CommandHandle:
    return await _append_command(
        session, scope, run_id, "cancel", idempotency_key, {}, actor=scope.actor_id
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
) -> CommandHandle:
    return await _append_command(
        session, scope, run_id, "pause", idempotency_key, {}, actor=scope.actor_id
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
) -> CommandHandle:
    return await _append_command(
        session, scope, run_id, "resume", idempotency_key, {}, actor=scope.actor_id
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
) -> CommandHandle:
    request = await _get_approval(session, scope, approval_id)
    Draft202012Validator(request.input_schema).validate(body.value)
    _reject_secret_material(body.value)
    return await _handle_approval(
        session, scope, request, "approve", idempotency_key, body.value, scope.actor_id
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
) -> CommandHandle:
    request = await _get_approval(session, scope, approval_id)
    return await _handle_approval(
        session, scope, request, "reject", idempotency_key, body.value, scope.actor_id
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
            "actor": scope.actor_id,
        },
        actor=scope.actor_id,
    )
    if request.handler_command_id not in {None, handle.command_id}:
        raise HTTPException(status_code=409, detail="input request already has a pending command")
    request.handler_command_id = handle.command_id
    request.handled_by = scope.actor_id
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
        actor=scope.actor_id,
    )
    task.last_retry_command_id = handle.command_id
    return handle


@router.get("/projects/{project_id}/commands/{command_id}", response_model=CommandHandle)
async def get_command(command_id: UUID, scope: Scope, session: Session) -> CommandHandle:
    return await commands.get(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        command_id=command_id,
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
        metrics = request.app.state.metrics
        metrics.sse_connections.add(1)
        try:
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
                        metrics.projection_lag.record(
                            max(0.0, (datetime.now(UTC) - item.occurred_at).total_seconds())
                        )
                        yield format_sse(item)
                    continue
                yield ": heartbeat\n\n"
                await asyncio.sleep(poll_interval)
        finally:
            metrics.sse_connections.add(-1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get(
    "/projects/{project_id}/runs/{run_id}/artifacts",
    response_model=ArtifactListResponse,
)
async def list_artifacts(run_id: UUID, scope: Scope, session: Session) -> ArtifactListResponse:
    await _get_scoped_run(session, scope, run_id)
    artifacts = list(
        await session.scalars(
            select(Artifact).where(
                Artifact.tenant_id == scope.tenant_id,
                Artifact.project_id == scope.project_id,
                Artifact.run_id == run_id,
            )
        )
    )
    return ArtifactListResponse(
        items=[_artifact_snapshot(item) for item in artifacts], total=len(artifacts)
    )


@router.post(
    "/projects/{project_id}/artifacts/{artifact_id}:download",
    response_model=ArtifactDownloadGrantResponse,
)
async def issue_artifact_download(
    artifact_id: UUID,
    scope: Scope,
    session: Session,
) -> ArtifactDownloadGrantResponse:
    artifact = await session.scalar(
        select(Artifact).where(
            Artifact.id == artifact_id,
            Artifact.tenant_id == scope.tenant_id,
            Artifact.project_id == scope.project_id,
        )
    )
    if artifact is None or artifact.status != "AVAILABLE":
        raise HTTPException(status_code=404, detail="artifact not found")
    if artifact.retention_until is not None and artifact.retention_until <= datetime.now(UTC):
        raise HTTPException(status_code=410, detail="artifact retention period expired")
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(minutes=5)
    grant = ArtifactDownloadGrant(
        tenant_id=scope.tenant_id,
        artifact_id=artifact.id,
        token_hash=hashlib.sha256(token.encode()).hexdigest(),
        issued_to=scope.actor_id,
        expires_at=expires_at,
    )
    session.add(grant)
    await AuditRepository().append(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        actor_id=scope.actor_id,
        action="artifact.download.issue",
        resource_type="artifact",
        resource_id=str(artifact.id),
        run_id=artifact.run_id,
    )
    return ArtifactDownloadGrantResponse(
        artifactId=artifact.id,
        downloadRef=(
            f"/v1/projects/{scope.project_id}/artifacts/{artifact.id}/content?grant={token}"
        ),
        expiresAt=expires_at,
    )


@router.get("/projects/{project_id}/artifacts/{artifact_id}/content")
async def download_artifact(
    artifact_id: UUID,
    grant: str,
    request: Request,
    scope: Scope,
    session: Session,
) -> Response:
    token_hash = hashlib.sha256(grant.encode()).hexdigest()
    download_grant = await session.scalar(
        select(ArtifactDownloadGrant)
        .where(
            ArtifactDownloadGrant.tenant_id == scope.tenant_id,
            ArtifactDownloadGrant.artifact_id == artifact_id,
            ArtifactDownloadGrant.token_hash == token_hash,
        )
        .with_for_update()
    )
    now = datetime.now(UTC)
    if (
        download_grant is None
        or download_grant.consumed_at is not None
        or download_grant.expires_at <= now
        or download_grant.issued_to != scope.actor_id
    ):
        raise HTTPException(status_code=410, detail="artifact download grant is invalid")
    artifact = await session.scalar(
        select(Artifact).where(
            Artifact.id == artifact_id,
            Artifact.tenant_id == scope.tenant_id,
            Artifact.project_id == scope.project_id,
            Artifact.status == "AVAILABLE",
        )
    )
    if artifact is None:
        raise HTTPException(status_code=404, detail="artifact not found")
    if artifact.retention_until is not None and artifact.retention_until <= now:
        raise HTTPException(status_code=410, detail="artifact retention period expired")
    settings = request.app.state.settings
    if settings.artifact_gateway_url:
        capability = ArtifactCapabilityIssuer(settings.artifact_capability_secret.encode()).issue(
            action="artifact.read",
            tenant_id=str(scope.tenant_id),
            project_id=str(scope.project_id),
            run_id=str(artifact.run_id),
            subject_id=scope.actor_id,
            artifact_id=str(artifact.id),
        )
        content = await asyncio.to_thread(
            _read_from_artifact_gateway,
            settings.artifact_gateway_url,
            artifact.id,
            capability,
            settings.workload_tls(),
        )
    else:
        root = Path(settings.artifact_root).resolve()
        target = (root / artifact.object_key).resolve()
        if not target.is_relative_to(root):
            raise HTTPException(status_code=500, detail="artifact object key is invalid")
        try:
            content = await asyncio.to_thread(target.read_bytes)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail="artifact bytes not found") from exc
    if hashlib.sha256(content).hexdigest() != artifact.sha256:
        raise HTTPException(status_code=500, detail="artifact integrity check failed")
    download_grant.consumed_at = now
    await AuditRepository().append(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        actor_id=scope.actor_id,
        action="artifact.read",
        resource_type="artifact",
        resource_id=str(artifact.id),
        run_id=artifact.run_id,
    )
    return Response(
        content=content,
        media_type=artifact.media_type,
        headers={"Content-Disposition": f'attachment; filename="{artifact.filename}"'},
    )


def _read_from_artifact_gateway(
    gateway_url: str,
    artifact_id: UUID,
    capability_token: str,
    workload_tls: WorkloadTls,
) -> bytes:
    query = urlencode({"capability_token": capability_token})
    request = UrlRequest(
        f"{gateway_url.rstrip('/')}/internal/v1/artifacts/{artifact_id}:read?{query}",
        data=b"",
        method="POST",
    )
    try:
        options: dict[str, Any] = {"timeout": 30}
        context = workload_tls.client_context()
        if context is not None:
            options["context"] = context
        with urlopen(request, **options) as response:
            return cast(bytes, response.read(100 * 1024 * 1024 + 1))
    except HTTPError as exc:
        raise HTTPException(status_code=exc.code, detail="Artifact Gateway rejected read") from exc
    except (URLError, TimeoutError) as exc:
        raise HTTPException(status_code=503, detail="Artifact Gateway unavailable") from exc


@router.get("/projects/{project_id}/audit-logs", response_model=AuditListResponse)
async def list_audit_logs(
    scope: Scope,
    session: Session,
    run_id: Annotated[UUID | None, Query(alias="runId")] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> AuditListResponse:
    items = list(
        await session.scalars(
            AuditRepository.query(
                tenant_id=scope.tenant_id,
                project_id=scope.project_id,
                run_id=run_id,
            ).limit(limit)
        )
    )
    return AuditListResponse(items=[_audit_snapshot(item) for item in items], total=len(items))


@router.post("/projects/{project_id}/audit-logs:export")
async def export_audit_logs(scope: Scope, session: Session) -> Response:
    items = list(
        await session.scalars(
            AuditRepository.query(tenant_id=scope.tenant_id, project_id=scope.project_id)
        )
    )
    content = "\n".join(
        json.dumps(
            _audit_snapshot(item).model_dump(mode="json", by_alias=True),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        for item in items
    )
    return Response(
        content=content + ("\n" if content else ""),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": "attachment; filename=audit.ndjson"},
    )


@router.post(
    "/projects/{project_id}/webhooks",
    response_model=WebhookSnapshot,
    status_code=201,
)
async def create_webhook(
    body: CreateWebhookRequest,
    request: Request,
    scope: Scope,
    session: Session,
) -> WebhookSnapshot:
    validate_secret_ref(body.secret_ref)
    validate_webhook_target(body.url, request.app.state.settings.webhook_allowed_hosts)
    endpoint = WebhookEndpoint(
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        url=body.url,
        secret_ref=body.secret_ref,
        event_types=sorted(set(body.event_types)),
    )
    session.add(endpoint)
    await session.flush()
    await AuditRepository().append(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        actor_id=scope.actor_id,
        action="webhook.create",
        resource_type="webhook_endpoint",
        resource_id=str(endpoint.id),
        metadata={"urlHost": body.url.split("/", 3)[2]},
    )
    return _webhook_snapshot(endpoint)


@router.get("/projects/{project_id}/webhooks", response_model=WebhookListResponse)
async def list_webhooks(scope: Scope, session: Session) -> WebhookListResponse:
    endpoints = list(
        await session.scalars(
            select(WebhookEndpoint).where(
                WebhookEndpoint.tenant_id == scope.tenant_id,
                WebhookEndpoint.project_id == scope.project_id,
            )
        )
    )
    return WebhookListResponse(
        items=[_webhook_snapshot(endpoint) for endpoint in endpoints],
        total=len(endpoints),
    )


async def _get_scoped_run(session: AsyncSession, scope: RequestScope, run_id: UUID) -> Run:
    run = await session.scalar(
        select(Run).where(Run.id == run_id, Run.tenant_id == scope.tenant_id)
    )
    if run is None or run.project_id != scope.project_id:
        raise HTTPException(status_code=404, detail="run not found")
    return run


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
    return await commands.append(
        session,
        tenant_id=scope.tenant_id,
        project_id=scope.project_id,
        run_id=run_id,
        command_type=command_type,
        idempotency_key=idempotency_key,
        payload=payload,
        actor=actor,
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
    if request.expires_at is not None and request.expires_at <= datetime.now(UTC):
        raise HTTPException(status_code=410, detail="approval request expired")
    if request.requires_distinct_approver and actor == request.requested_by:
        raise HTTPException(status_code=403, detail="critical approval requires maker-checker")
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


def _artifact_snapshot(artifact: Artifact) -> ArtifactSnapshot:
    return ArtifactSnapshot(
        artifactId=artifact.id,
        runId=artifact.run_id,
        kind=artifact.kind,
        filename=artifact.filename,
        mediaType=artifact.media_type,
        sizeBytes=artifact.size_bytes,
        sha256=artifact.sha256,
        status=artifact.status,
        version=artifact.version,
        retentionUntil=artifact.retention_until,
    )


def _audit_snapshot(item: AuditLog) -> AuditSnapshot:
    return AuditSnapshot(
        auditId=item.id,
        actorId=item.actor_id,
        action=item.action,
        resourceType=item.resource_type,
        resourceId=item.resource_id,
        outcome=item.outcome,
        policyRevision=item.policy_revision,
        runId=item.run_id,
        metadata=item.metadata_json,
        occurredAt=item.occurred_at,
    )


def _webhook_snapshot(endpoint: WebhookEndpoint) -> WebhookSnapshot:
    return WebhookSnapshot(
        endpointId=endpoint.id,
        url=endpoint.url,
        secretRef=endpoint.secret_ref,
        eventTypes=endpoint.event_types,
        status=endpoint.status,
        failureCount=endpoint.failure_count,
        createdAt=endpoint.created_at,
    )


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
        editorState=EditorState.model_validate(draft.editor_state),
        diagnostics=draft.diagnostics,
        updatedBy=draft.updated_by,
        updatedAt=draft.updated_at,
    )


def _project_configuration_snapshot(
    item: ProjectConfiguration,
) -> ProjectConfigurationSnapshot:
    return ProjectConfigurationSnapshot(
        configurationId=item.id,
        kind=cast(Literal["agent", "tool", "model"], item.kind),
        name=item.name,
        sourceRef=item.source_ref,
        configuration=item.configuration,
        revision=item.revision,
        createdBy=item.created_by,
        updatedBy=item.updated_by,
        createdAt=item.created_at,
        updatedAt=item.updated_at,
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
