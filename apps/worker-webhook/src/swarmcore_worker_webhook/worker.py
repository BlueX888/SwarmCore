from __future__ import annotations

import asyncio
import socket
import ssl
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from swarmcore_governance import (
    PolicyEngine,
    PolicyRequest,
    PolicySubject,
    SecretProvider,
    WebhookEnvelope,
    WebhookSigner,
    validate_webhook_target,
)
from swarmcore_observability import SwarmMetrics, get_tracer
from swarmcore_persistence import AuditRepository, tenant_transaction
from swarmcore_persistence.models import OutboxEvent, WebhookDelivery, WebhookEndpoint
from swarmcore_persistence.repositories import pending_outbox_query


class WebhookWorker:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        policy: PolicyEngine,
        secrets: SecretProvider,
        *,
        worker_id: str,
        allowed_hosts: frozenset[str],
        batch_size: int = 50,
        metrics: SwarmMetrics | None = None,
    ) -> None:
        self._sessions = sessions
        self._policy = policy
        self._secrets = secrets
        self._worker_id = worker_id
        self._allowed_hosts = allowed_hosts
        self._batch_size = batch_size
        self._metrics = metrics

    async def run_once(self) -> int:
        claimed = await self._claim()
        for outbox_id in claimed:
            await self._process(outbox_id)
        return len(claimed)

    async def _claim(self) -> list[UUID]:
        now = datetime.now(UTC)
        claimed: list[UUID] = []
        async with self._sessions() as session, session.begin():
            rows = list(
                await session.scalars(
                    pending_outbox_query("webhook", limit=self._batch_size)
                )
            )
            for row in rows:
                row.status = "DELIVERING"
                row.locked_by = self._worker_id
                row.locked_until = now + timedelta(seconds=30)
                claimed.append(row.id)
        return claimed

    async def _process(self, outbox_id: UUID) -> None:
        async with self._sessions() as session:
            outbox = await session.get(OutboxEvent, outbox_id)
            if outbox is None or outbox.status != "DELIVERING":
                return
            tenant_id = outbox.tenant_id
            project_id = UUID(str(outbox.payload["projectId"]))
            delivery_id = UUID(str(outbox.payload["deliveryId"]))
            event = dict(outbox.payload["event"])
            event_type = outbox.type
        try:
            with get_tracer("worker-webhook").start_as_current_span(
                "webhook.deliver",
                attributes={
                    "tenant.id": str(tenant_id),
                    "project.id": str(project_id),
                    "swarm.run.id": str(event.get("runId", "unknown")),
                    "webhook.event_type": event_type,
                },
            ) as span:
                try:
                    await self._deliver(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        delivery_id=delivery_id,
                        event_type=event_type,
                        event=event,
                    )
                except Exception as exc:
                    span.set_attribute("error.type", type(exc).__name__)
                    raise
        except Exception as exc:
            if self._metrics is not None:
                self._metrics.webhook_deliveries.add(1, {"status": "failed"})
            await self._retry(outbox_id, tenant_id, project_id, delivery_id, exc)
        else:
            if self._metrics is not None:
                self._metrics.webhook_deliveries.add(1, {"status": "succeeded"})
            async with self._sessions() as session, session.begin():
                outbox = await session.get(OutboxEvent, outbox_id, with_for_update=True)
                if outbox is not None:
                    outbox.status = "DELIVERED"
                    outbox.delivered_at = datetime.now(UTC)
                    outbox.locked_by = None
                    outbox.locked_until = None

    async def _deliver(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        delivery_id: UUID,
        event_type: str,
        event: dict[str, Any],
    ) -> None:
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            delivery = await session.get(WebhookDelivery, delivery_id, with_for_update=True)
            if delivery is None or delivery.status == "DELIVERED":
                return
            endpoint = await session.get(WebhookEndpoint, delivery.endpoint_id)
            if endpoint is None or endpoint.status != "ACTIVE":
                raise RuntimeError("webhook endpoint is unavailable")
            decision = (
                await self._policy.evaluate(
                    PolicyRequest(
                        subject=PolicySubject(
                            id=self._worker_id,
                            tenantId=str(tenant_id),
                            roles=("workload",),
                        ),
                        action="webhook.deliver",
                        resource={
                            "projectId": str(project_id),
                            "endpointId": str(endpoint.id),
                            "url": endpoint.url,
                        },
                        context={"eventType": event_type},
                    )
                )
            ).enforce()
            payload = _redact(event, set(decision.obligations.redact_fields))
            envelope = WebhookEnvelope(
                delivery.delivery_id,
                int(datetime.now(UTC).timestamp()),
                event_type,
                payload,
            )
            async with self._secrets.lease(endpoint.secret_ref) as lease:
                signing_key = lease.values.get("signingKey")
                if signing_key is None:
                    raise RuntimeError("webhook Secret must contain signingKey")
                signature = WebhookSigner(signing_key.encode()).sign(envelope)
                status = await asyncio.to_thread(
                    _post_https,
                    endpoint.url,
                    envelope.body(),
                    signature,
                    delivery.delivery_id,
                    self._allowed_hosts,
                )
            if status < 200 or status >= 300:
                raise RuntimeError(f"webhook returned HTTP {status}")
            delivery.status = "DELIVERED"
            delivery.attempts += 1
            delivery.response_status = status
            delivery.delivered_at = datetime.now(UTC)
            endpoint.failure_count = 0
            await AuditRepository().append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id=self._worker_id,
                action="webhook.deliver",
                resource_type="webhook_endpoint",
                resource_id=str(endpoint.id),
                policy_revision=decision.policy_revision,
                metadata={"deliveryId": delivery.delivery_id, "status": status},
            )

    async def _retry(
        self,
        outbox_id: UUID,
        tenant_id: UUID,
        project_id: UUID,
        delivery_id: UUID,
        exc: Exception,
    ) -> None:
        attempts = 1
        async with tenant_transaction(
            self._sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            delivery = await session.get(WebhookDelivery, delivery_id, with_for_update=True)
            if delivery is not None:
                delivery.attempts += 1
                attempts = delivery.attempts
                delivery.last_error = f"{type(exc).__name__}: {exc}"[:2000]
                delivery.next_attempt_at = datetime.now(UTC) + timedelta(
                    seconds=min(3600, 2 ** min(attempts, 11))
                )
                endpoint = await session.get(WebhookEndpoint, delivery.endpoint_id)
                if endpoint is not None:
                    endpoint.failure_count += 1
                    if endpoint.failure_count >= 10:
                        endpoint.status = "DISABLED"
                        delivery.status = "DEAD"
        async with self._sessions() as session, session.begin():
            outbox = await session.get(OutboxEvent, outbox_id, with_for_update=True)
            if outbox is not None:
                outbox.attempts = attempts
                outbox.last_error = f"{type(exc).__name__}: {exc}"[:4000]
                outbox.status = "PENDING" if attempts < 10 else "DEAD"
                outbox.available_at = datetime.now(UTC) + timedelta(
                    seconds=min(3600, 2 ** min(attempts, 11))
                )
                outbox.locked_by = None
                outbox.locked_until = None


def _redact(value: Any, fields: set[str]) -> Any:
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key in fields else _redact(item, fields)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item, fields) for item in value]
    return value


def _post_https(
    url: str,
    body: bytes,
    signature: str,
    delivery_id: str,
    allowed_hosts: frozenset[str],
) -> int:
    hostname, port, addresses = validate_webhook_target(url, allowed_hosts)
    parsed = urlsplit(url)
    path = parsed.path or "/"
    if parsed.query:
        path += f"?{parsed.query}"
    raw = socket.create_connection((addresses[0], port), timeout=10)
    try:
        tls = ssl.create_default_context().wrap_socket(raw, server_hostname=hostname)
        try:
            request = (
                f"POST {path} HTTP/1.1\r\nHost: {hostname}\r\n"
                "Content-Type: application/json\r\n"
                f"Content-Length: {len(body)}\r\n"
                f"X-Swarm-Signature: {signature}\r\n"
                f"X-Swarm-Delivery: {delivery_id}\r\nConnection: close\r\n\r\n"
            ).encode() + body
            tls.sendall(request)
            response = b""
            while b"\r\n" not in response and len(response) <= 64 * 1024:
                chunk = tls.recv(4096)
                if not chunk:
                    break
                response += chunk
        finally:
            tls.close()
    finally:
        raw.close()
    try:
        return int(response.split(b"\r\n", 1)[0].split()[1])
    except (IndexError, ValueError) as exc:
        raise RuntimeError("webhook returned an invalid HTTP response") from exc
