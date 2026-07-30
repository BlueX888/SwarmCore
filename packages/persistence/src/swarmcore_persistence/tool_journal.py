from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from swarmcore_domain import uuid7
from swarmcore_tool_gateway import EffectConflict, EffectReservation

from .database import tenant_transaction
from .models import ToolEffect


class PostgresEffectJournal:
    _lease_seconds = 45

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def reserve(
        self,
        *,
        tenant_id: str,
        project_id: str,
        run_id: str,
        node_key: str,
        tool_ref: str,
        effect_id: str,
        request_hash: str,
    ) -> EffectReservation:
        tenant_uuid = UUID(tenant_id)
        project_uuid = UUID(project_id)
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_uuid, project_id=project_uuid
        ) as session:
            statement = (
                insert(ToolEffect)
                .values(
                    id=uuid7(),
                    tenant_id=tenant_uuid,
                    project_id=project_uuid,
                    run_id=UUID(run_id),
                    node_key=node_key,
                    tool_ref=tool_ref,
                    effect_id=effect_id,
                    request_hash=request_hash,
                    status="PENDING",
                    attempts=1,
                    lease_expires_at=datetime.now(UTC)
                    + timedelta(seconds=self._lease_seconds),
                    lease_owner=(lease_owner := uuid4().hex),
                    lease_generation=1,
                )
                .on_conflict_do_nothing(constraint="uq_tool_effect_scope")
                .returning(ToolEffect.id)
            )
            inserted = await session.scalar(statement)
            if inserted is not None:
                return EffectReservation(
                    owner=True,
                    lease_owner=lease_owner,
                    lease_generation=1,
                )
            effect = await self._get_for_update(
                session, tenant_uuid, project_uuid, tool_ref, effect_id
            )
            if effect.request_hash != request_hash:
                raise EffectConflict("effect id was reused with different input")
            if effect.status == "SUCCEEDED":
                return EffectReservation(owner=False, output=effect.output)
            if effect.status == "FAILED":
                lease_owner = uuid4().hex
                effect.status = "PENDING"
                effect.error = None
                effect.attempts += 1
                effect.lease_expires_at = datetime.now(UTC) + timedelta(
                    seconds=self._lease_seconds
                )
                effect.lease_owner = lease_owner
                effect.lease_generation += 1
                return EffectReservation(
                    owner=True,
                    lease_owner=lease_owner,
                    lease_generation=effect.lease_generation,
                )
            if effect.lease_expires_at <= datetime.now(UTC):
                lease_owner = uuid4().hex
                effect.attempts += 1
                effect.lease_expires_at = datetime.now(UTC) + timedelta(
                    seconds=self._lease_seconds
                )
                effect.lease_owner = lease_owner
                effect.lease_generation += 1
                return EffectReservation(
                    owner=True,
                    lease_owner=lease_owner,
                    lease_generation=effect.lease_generation,
                )
            return EffectReservation(owner=False)

    async def complete(
        self,
        *,
        tenant_id: str,
        project_id: str,
        tool_ref: str,
        effect_id: str,
        lease_owner: str,
        lease_generation: int,
        output: dict[str, Any],
    ) -> bool:
        tenant_uuid = UUID(tenant_id)
        project_uuid = UUID(project_id)
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_uuid, project_id=project_uuid
        ) as session:
            changed = await session.scalar(
                update(ToolEffect)
                .where(
                    ToolEffect.tenant_id == tenant_uuid,
                    ToolEffect.project_id == project_uuid,
                    ToolEffect.tool_ref == tool_ref,
                    ToolEffect.effect_id == effect_id,
                    ToolEffect.status == "PENDING",
                    ToolEffect.lease_owner == lease_owner,
                    ToolEffect.lease_generation == lease_generation,
                )
                .values(output=output, status="SUCCEEDED", lease_owner=None)
                .returning(ToolEffect.id)
            )
            return changed is not None

    async def fail(
        self,
        *,
        tenant_id: str,
        project_id: str,
        tool_ref: str,
        effect_id: str,
        lease_owner: str,
        lease_generation: int,
        error: str,
    ) -> bool:
        tenant_uuid = UUID(tenant_id)
        project_uuid = UUID(project_id)
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_uuid, project_id=project_uuid
        ) as session:
            changed = await session.scalar(
                update(ToolEffect)
                .where(
                    ToolEffect.tenant_id == tenant_uuid,
                    ToolEffect.project_id == project_uuid,
                    ToolEffect.tool_ref == tool_ref,
                    ToolEffect.effect_id == effect_id,
                    ToolEffect.status == "PENDING",
                    ToolEffect.lease_owner == lease_owner,
                    ToolEffect.lease_generation == lease_generation,
                )
                .values(error=error, status="FAILED", lease_owner=None)
                .returning(ToolEffect.id)
            )
            return changed is not None

    async def renew(
        self,
        *,
        tenant_id: str,
        project_id: str,
        tool_ref: str,
        effect_id: str,
        lease_owner: str,
        lease_generation: int,
    ) -> bool:
        tenant_uuid = UUID(tenant_id)
        project_uuid = UUID(project_id)
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_uuid, project_id=project_uuid
        ) as session:
            changed = await session.scalar(
                update(ToolEffect)
                .where(
                    ToolEffect.tenant_id == tenant_uuid,
                    ToolEffect.project_id == project_uuid,
                    ToolEffect.tool_ref == tool_ref,
                    ToolEffect.effect_id == effect_id,
                    ToolEffect.status == "PENDING",
                    ToolEffect.lease_owner == lease_owner,
                    ToolEffect.lease_generation == lease_generation,
                )
                .values(
                    lease_expires_at=datetime.now(UTC)
                    + timedelta(seconds=self._lease_seconds)
                )
                .returning(ToolEffect.id)
            )
            return changed is not None

    @staticmethod
    async def _get_for_update(
        session: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
        tool_ref: str,
        effect_id: str,
    ) -> ToolEffect:
        effect = await session.scalar(
            select(ToolEffect)
            .where(
                ToolEffect.tenant_id == tenant_id,
                ToolEffect.project_id == project_id,
                ToolEffect.tool_ref == tool_ref,
                ToolEffect.effect_id == effect_id,
            )
            .with_for_update()
        )
        if effect is None:
            raise RuntimeError("tool effect does not exist")
        return effect
