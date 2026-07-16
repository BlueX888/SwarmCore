from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_persistence import Database, tenant_transaction


@dataclass(frozen=True)
class RequestScope:
    tenant_id: UUID
    project_id: UUID


async def request_scope(
    project_id: UUID,
    x_tenant_id: Annotated[UUID, Header(alias="X-Tenant-ID")],
) -> RequestScope:
    return RequestScope(tenant_id=x_tenant_id, project_id=project_id)


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
