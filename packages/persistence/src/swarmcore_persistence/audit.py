from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_domain import uuid7

from .models import AuditLog


class AuditRepository:
    async def append(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        outcome: str = "ALLOWED",
        policy_revision: str | None = None,
        run_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> AuditLog:
        record = AuditLog(
            id=uuid7(),
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            policy_revision=policy_revision,
            metadata_json=metadata or {},
            trace_id=trace_id,
            occurred_at=datetime.now(UTC),
        )
        session.add(record)
        await session.flush()
        return record

    @staticmethod
    def query(
        *, tenant_id: UUID, project_id: UUID, run_id: UUID | None = None
    ) -> Select[tuple[AuditLog]]:
        query = select(AuditLog).where(
            AuditLog.tenant_id == tenant_id,
            AuditLog.project_id == project_id,
        )
        if run_id is not None:
            query = query.where(AuditLog.run_id == run_id)
        return query.order_by(AuditLog.occurred_at, AuditLog.id)
