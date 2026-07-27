from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_governance import PolicyRequest, PolicySubject, redact_policy_log
from swarmcore_persistence import AuditRepository, Database, tenant_transaction
from swarmcore_persistence.models import Project

from .authentication import AuthenticationError, Identity, JwtAuthenticator

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RequestScope:
    tenant_id: UUID
    project_id: UUID
    actor_id: str
    roles: tuple[str, ...]
    scopes: tuple[str, ...]
    auth_context_hash: str


async def request_scope(
    project_id: UUID,
    request: Request,
    x_tenant_id: Annotated[UUID | None, Header(alias="X-Tenant-ID")] = None,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_actor_id: Annotated[str, Header(alias="X-Actor-ID")] = "local-user",
    x_roles: Annotated[str, Header(alias="X-Roles")] = "tenant_admin",
    x_scopes: Annotated[str, Header(alias="X-Scopes")] = "",
) -> RequestScope:
    settings = request.app.state.settings
    if settings.auth_mode == "jwt":
        try:
            authenticator = getattr(request.app.state, "jwt_authenticator", None)
            if authenticator is None:
                authenticator = JwtAuthenticator(settings)
                request.app.state.jwt_authenticator = authenticator
            identity = authenticator.authenticate(authorization or "")
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
    else:
        if x_tenant_id is None:
            raise HTTPException(status_code=401, detail="X-Tenant-ID is required in local mode")
        identity = Identity(
            subject_id=x_actor_id,
            tenant_id=x_tenant_id,
            roles=tuple(value.strip() for value in x_roles.split(",") if value.strip()),
            scopes=tuple(value.strip() for value in x_scopes.split(",") if value.strip()),
            issuer="local-development",
            audience="swarmcore-api",
            project_scopes=((str(project_id), ()),),
        )
    if not identity.can_access_project(project_id):
        raise HTTPException(status_code=403, detail="project scope does not grant access")
    effective_scopes = identity.scopes_for(project_id)
    request.state.tenant_id = identity.tenant_id
    request.state.project_id = project_id
    if request.path_params.get("run_id") is not None:
        request.state.run_id = request.path_params["run_id"]
    return RequestScope(
        tenant_id=identity.tenant_id,
        project_id=project_id,
        actor_id=identity.subject_id,
        roles=identity.roles,
        scopes=effective_scopes,
        auth_context_hash=identity.context_hash,
    )


async def authorize_rest(
    request: Request,
    scope: Annotated[RequestScope, Depends(request_scope)],
) -> None:
    action = _rest_action(request.method, request.url.path)
    policy_request = PolicyRequest(
        subject=PolicySubject(
            id=scope.actor_id,
            tenantId=str(scope.tenant_id),
            roles=scope.roles,
            scopes=scope.scopes,
        ),
        action=action,
        resource={"projectId": str(scope.project_id), "path": request.url.path},
    )
    decision = await request.app.state.policy.evaluate(policy_request)
    if not decision.allow:
        request.app.state.metrics.policy_denied.add(1, {"action": action})
        logger.warning(
            "policy denied request",
            extra={"event": "policy.denied", "fields": redact_policy_log(policy_request, decision)},
        )
        if request.app.state.settings.policy_mode == "opa":
            database: Database = request.app.state.database
            async with tenant_transaction(
                database.sessions, tenant_id=scope.tenant_id, project_id=scope.project_id
            ) as session:
                if await session.get(Project, scope.project_id) is not None:
                    await AuditRepository().append(
                        session,
                        tenant_id=scope.tenant_id,
                        project_id=scope.project_id,
                        actor_id=scope.actor_id,
                        action="policy.deny",
                        resource_type="api_route",
                        resource_id=request.url.path,
                        outcome="DENIED",
                        policy_revision=decision.policy_revision,
                        metadata={"requestedAction": action},
                    )
        raise HTTPException(status_code=403, detail="POLICY_DENIED")


def _rest_action(method: str, path: str) -> str:
    if path.endswith("/capability-center"):
        return "capability.read"
    if path.endswith("/capability-runs"):
        return "run.create"
    if "/presets" in path:
        return "strategy.read" if method == "GET" else "strategy.write"
    if "/capability-packs" in path:
        return "capability.read" if method == "GET" else "capability.manage"
    if "/business-works/invoice-assurance/batches" in path:
        return "case.read" if method == "GET" else "case.assess"
    if path.endswith("/business-works/invoice-assurance/rule-trends"):
        return "case.read"
    if "/business-works" in path:
        return "capability.read" if method == "GET" else "capability.manage"
    if "/rule-set" in path:
        return "rule.read" if method == "GET" else "rule.manage"
    if "/findings" in path:
        return "finding.read" if method == "GET" else "finding.act"
    if "/reports" in path:
        return "report.read"
    if "/attachments" in path:
        return "blob.read" if method == "GET" else "blob.write"
    if "/work-items" in path:
        if method == "GET":
            return "work-item.read"
        return "work-item.execute" if path.endswith(":execute") else "work-item.write"
    if "/evaluations" in path:
        return "work-item.read" if method == "GET" else "evaluation.write"
    if "/configurations/" in path:
        return "strategy.read" if method == "GET" else "strategy.write"
    if "/strategies" in path:
        return "strategy.read" if method == "GET" else "strategy.write"
    if "/approvals" in path:
        return "approval.read" if method == "GET" else "approval.decide"
    if "/inputs" in path:
        return "run.read" if method == "GET" else "run.control"
    if "/artifacts" in path:
        read = method == "GET" or path.endswith(":download")
        return "artifact.read" if read else "artifact.write"
    if "/audit-logs" in path:
        return "audit.read"
    if "/webhooks" in path:
        return "webhook.read" if method == "GET" else "webhook.write"
    if method == "GET":
        return "run.read"
    return "run.create" if path.endswith("/runs") else "run.control"


async def db_session(
    request: Request,
    scope: Annotated[RequestScope, Depends(request_scope)],
) -> AsyncIterator[AsyncSession]:
    database: Database = request.app.state.database
    async with tenant_transaction(
        database.sessions, tenant_id=scope.tenant_id, project_id=scope.project_id
    ) as session:
        yield session


def require_idempotency_key(
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> str:
    if not idempotency_key or len(idempotency_key) > 256:
        raise HTTPException(status_code=400, detail="a valid Idempotency-Key is required")
    return idempotency_key
