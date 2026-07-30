from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from swarmcore_domain import uuid7
from swarmcore_observability import SwarmMetrics
from swarmcore_persistence import (
    OutboxClaim,
    OutboxLeaseKeeper,
    claim_outbox,
    owns_outbox_claim,
    tenant_transaction,
)
from swarmcore_persistence.models import (
    OutboxEvent,
    WebhookDelivery,
    WebhookEndpoint,
)
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
        metrics: SwarmMetrics | None = None,
    ) -> None:
        self._sessions = sessions
        self._jetstream = jetstream
        self._worker_id = worker_id
        self._batch_size = batch_size
        self._metrics = metrics
        self._last_pending = 0

    async def run_once(self) -> int:
        claimed = await self._claim()
        for claim in claimed:
            try:
                async with OutboxLeaseKeeper(
                    self._sessions, claim, worker_id=self._worker_id
                ):
                    await self._publish(claim)
            except Exception as exc:
                await self._retry(claim, str(exc))
        return len(claimed)

    async def _claim(self) -> list[OutboxClaim]:
        now = datetime.now(UTC)
        claimed: list[OutboxClaim] = []
        async with self._sessions() as session, session.begin():
            pending = int(
                await session.scalar(
                    select(func.count(OutboxEvent.id)).where(
                        OutboxEvent.destination == "nats",
                        OutboxEvent.status == "PENDING",
                    )
                )
                or 0
            )
            events = list(await session.scalars(pending_nats_outbox_query(limit=self._batch_size)))
            for event in events:
                claimed.append(claim_outbox(event, worker_id=self._worker_id, now=now))
                if self._metrics is not None:
                    self._metrics.queue_schedule_latency.record(
                        max(0.0, (now - event.available_at).total_seconds()),
                        {"queue": "nats"},
                    )
        if self._metrics is not None:
            self._metrics.outbox_pending.add(
                pending - self._last_pending, {"destination": "nats"}
            )
            self._last_pending = pending
        return claimed

    async def _publish(self, claim: OutboxClaim) -> None:
        async with self._sessions() as session:
            event = await session.get(OutboxEvent, claim.id)
            if event is None or not owns_outbox_claim(
                event, claim, worker_id=self._worker_id
            ):
                return
            tenant_id = str(event.tenant_id)
            run_id = str(event.aggregate_id)
            payload = json.dumps(
                event.payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode()
            source_id = str(event.source_id)
            project_id = UUID(str(event.payload["projectId"]))
            source_uuid = event.source_id
            event_type = event.type
            event_payload = dict(event.payload)
        await self._jetstream.publish(
            f"swarm.events.{tenant_id}.{run_id}",
            payload,
            headers={"Nats-Msg-Id": source_id},
        )
        await self._enqueue_webhooks(
            tenant_id=UUID(tenant_id),
            project_id=project_id,
            run_id=UUID(run_id),
            event_id=source_uuid,
            event_type=event_type,
            payload=event_payload,
        )
        async with self._sessions() as session, session.begin():
            event = await session.get(OutboxEvent, claim.id, with_for_update=True)
            if event is not None and owns_outbox_claim(
                event, claim, worker_id=self._worker_id
            ):
                event.status = "DELIVERED"
                event.delivered_at = datetime.now(UTC)
                event.locked_by = None
                event.locked_until = None

    async def _enqueue_webhooks(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        run_id: UUID,
        event_id: UUID,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            endpoints = list(
                await session.scalars(
                    select(WebhookEndpoint).where(
                        WebhookEndpoint.tenant_id == tenant_id,
                        WebhookEndpoint.project_id == project_id,
                        WebhookEndpoint.status == "ACTIVE",
                        or_(
                            WebhookEndpoint.event_types == [],
                            WebhookEndpoint.event_types.contains([event_type]),
                        ),
                    )
                )
            )
            for endpoint in endpoints:
                existing = await session.scalar(
                    select(WebhookDelivery.id).where(
                        WebhookDelivery.endpoint_id == endpoint.id,
                        WebhookDelivery.event_id == event_id,
                    )
                )
                if existing is not None:
                    continue
                delivery = WebhookDelivery(
                    id=uuid7(),
                    tenant_id=tenant_id,
                    endpoint_id=endpoint.id,
                    event_id=event_id,
                    delivery_id=str(uuid7()),
                    next_attempt_at=datetime.now(UTC),
                )
                session.add(delivery)
                await session.flush()
                session.add(
                    OutboxEvent(
                        tenant_id=tenant_id,
                        aggregate_id=run_id,
                        destination="webhook",
                        partition_key=str(endpoint.id),
                        source_id=delivery.id,
                        type=event_type,
                        payload={
                            "projectId": str(project_id),
                            "endpointId": str(endpoint.id),
                            "deliveryId": str(delivery.id),
                            "event": payload,
                        },
                    )
                )

    async def _retry(self, claim: OutboxClaim, error: str) -> None:
        if self._metrics is not None:
            self._metrics.activity_retries.add(1, {"category": "event_publish"})
        async with self._sessions() as session, session.begin():
            event = await session.get(OutboxEvent, claim.id, with_for_update=True)
            if event is None or not owns_outbox_claim(
                event, claim, worker_id=self._worker_id
            ):
                return
            event.attempts += 1
            event.status = "PENDING"
            event.available_at = datetime.now(UTC) + timedelta(
                seconds=min(300, 2 ** min(event.attempts, 9))
            )
            event.last_error = error[:4000]
            event.locked_by = None
            event.locked_until = None
