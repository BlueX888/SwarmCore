from __future__ import annotations

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .models import OutboxEvent


@dataclass(frozen=True, slots=True)
class OutboxClaim:
    id: UUID
    generation: int


def claim_outbox(
    event: OutboxEvent,
    *,
    worker_id: str,
    now: datetime,
    lease_seconds: int = 30,
) -> OutboxClaim:
    event.status = "DELIVERING"
    event.locked_by = worker_id
    event.locked_until = now + timedelta(seconds=lease_seconds)
    event.lock_generation += 1
    return OutboxClaim(id=event.id, generation=event.lock_generation)


def owns_outbox_claim(
    event: OutboxEvent,
    claim: OutboxClaim,
    *,
    worker_id: str,
) -> bool:
    return (
        event.status == "DELIVERING"
        and event.locked_by == worker_id
        and event.lock_generation == claim.generation
    )


class OutboxLeaseKeeper:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        claim: OutboxClaim,
        *,
        worker_id: str,
        lease_seconds: int = 30,
    ) -> None:
        self._sessions = sessions
        self._claim = claim
        self._worker_id = worker_id
        self._lease_seconds = lease_seconds
        self._stop = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self.lost = False

    async def __aenter__(self) -> OutboxLeaseKeeper:
        self._task = asyncio.create_task(self._run())
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        self._stop.set()
        if self._task is None:
            return
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task

    async def _run(self) -> None:
        interval = max(1.0, self._lease_seconds / 3)
        while not self._stop.is_set():
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval)
            except TimeoutError:
                try:
                    renewed = await self._renew()
                except Exception:
                    self.lost = True
                    return
                if not renewed:
                    self.lost = True
                    return

    async def _renew(self) -> bool:
        async with self._sessions() as session, session.begin():
            renewed = await session.scalar(
                update(OutboxEvent)
                .where(
                    OutboxEvent.id == self._claim.id,
                    OutboxEvent.status == "DELIVERING",
                    OutboxEvent.locked_by == self._worker_id,
                    OutboxEvent.lock_generation == self._claim.generation,
                )
                .values(
                    locked_until=datetime.now(UTC)
                    + timedelta(seconds=self._lease_seconds)
                )
                .returning(OutboxEvent.id)
            )
            return renewed is not None
