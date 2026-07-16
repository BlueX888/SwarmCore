from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from swarmcore_persistence.models import OutboxEvent
from swarmcore_persistence.repositories import pending_nats_outbox_query


class JetStreamPublisher(Protocol):
    async def publish(self, subject: str, payload: bytes, *, headers: dict[str, str]) -> Any: ...


class EventPublisher:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        jetstream: JetStreamPublisher,
        *,
        worker_id: str,
        batch_size: int = 100,
    ) -> None:
        self._sessions = sessions
        self._jetstream = jetstream
        self._worker_id = worker_id
        self._batch_size = batch_size

    async def run_once(self) -> int:
        claimed = await self._claim()
        for event_id in claimed:
            try:
                await self._publish(event_id)
            except Exception as exc:
                await self._retry(event_id, str(exc))
        return len(claimed)

    async def _claim(self) -> list[UUID]:
        now = datetime.now(UTC)
        claimed: list[UUID] = []
        async with self._sessions() as session, session.begin():
            events = list(await session.scalars(pending_nats_outbox_query(limit=self._batch_size)))
            for event in events:
                event.status = "DELIVERING"
                event.locked_by = self._worker_id
                event.locked_until = now + timedelta(seconds=30)
                claimed.append(event.id)
        return claimed

    async def _publish(self, event_id: UUID) -> None:
        async with self._sessions() as session:
            event = await session.get(OutboxEvent, event_id)
            if event is None or event.status != "DELIVERING":
                return
            tenant_id = str(event.tenant_id)
            run_id = str(event.aggregate_id)
            payload = json.dumps(
                event.payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode()
            source_id = str(event.source_id)
        await self._jetstream.publish(
            f"swarm.events.{tenant_id}.{run_id}",
            payload,
            headers={"Nats-Msg-Id": source_id},
        )
        async with self._sessions() as session, session.begin():
            event = await session.get(OutboxEvent, event_id, with_for_update=True)
            if event is not None:
                event.status = "DELIVERED"
                event.delivered_at = datetime.now(UTC)
                event.locked_by = None
                event.locked_until = None

    async def _retry(self, event_id: UUID, error: str) -> None:
        async with self._sessions() as session, session.begin():
            event = await session.get(OutboxEvent, event_id, with_for_update=True)
            if event is None:
                return
            event.attempts += 1
            event.status = "PENDING"
            event.available_at = datetime.now(UTC) + timedelta(
                seconds=min(300, 2 ** min(event.attempts, 9))
            )
            event.last_error = error[:4000]
            event.locked_by = None
            event.locked_until = None
