from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from queue import Queue
from threading import Thread
from typing import Any, cast
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

import asyncpg
import boto3
import pytest
from fastapi.testclient import TestClient
from runtime_harness import RuntimeHarness
from sqlalchemy import func, select, update
from swarmcore_compiler import sequential
from swarmcore_governance import (
    InMemorySecretProvider,
    ModelCapabilityIssuer,
    RolePolicyEngine,
    S3ArtifactStore,
    VaultSecretProvider,
    WebhookEnvelope,
    WebhookSigner,
)
from swarmcore_model_gateway.main import Settings as ModelGatewaySettings
from swarmcore_model_gateway.main import create_app as create_model_gateway
from swarmcore_persistence import tenant_transaction
from swarmcore_persistence.models import (
    ModelUsageRecord,
    OutboxEvent,
    Run,
    RunCommand,
    WebhookDelivery,
    WebhookEndpoint,
)
from swarmcore_worker_webhook.worker import WebhookWorker


@pytest.mark.asyncio
async def test_s3_staging_is_tenant_scoped_and_cleaned() -> None:
    endpoint = os.getenv("SWARMCORE_TEST_S3_ENDPOINT")
    if not endpoint:
        pytest.skip("SWARMCORE_TEST_S3_ENDPOINT is not configured")
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name="us-east-1",
        aws_access_key_id=os.environ["SWARMCORE_TEST_S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["SWARMCORE_TEST_S3_SECRET_KEY"],
    )
    bucket = f"swarmcore-integration-{uuid4().hex}"
    client.create_bucket(Bucket=bucket)
    store = S3ArtifactStore(client, bucket)
    key = f"{uuid4()}/{uuid4()}/{uuid4()}/{uuid4()}/v1"
    try:
        await store.put(key, b"provider-integration")
        assert await store.get(key) == b"provider-integration"
        staging = client.list_objects_v2(Bucket=bucket, Prefix=f"{key.split('/', 1)[0]}/staging/")
        assert staging.get("KeyCount") == 0
    finally:
        await store.delete(key)
        client.delete_bucket(Bucket=bucket)


@pytest.mark.asyncio
async def test_vault_dynamic_database_lease_is_revoked() -> None:
    address = os.getenv("SWARMCORE_TEST_VAULT_ADDRESS")
    token = os.getenv("SWARMCORE_TEST_VAULT_TOKEN")
    if not address or not token:
        pytest.skip("Vault integration settings are not configured")
    mount = f"database-{uuid4().hex}"
    role = "readonly"
    headers = {"X-Vault-Token": token, "Content-Type": "application/json"}
    _vault_write(address, headers, f"v1/sys/mounts/{mount}", {"type": "database"})
    try:
        _vault_write(
            address,
            headers,
            f"v1/{mount}/config/swarmcore",
            {
                "plugin_name": "postgresql-database-plugin",
                "allowed_roles": role,
                "connection_url": (
                    "postgresql://{{username}}:{{password}}@postgres:5432/"
                    "swarmcore_test?sslmode=disable"
                ),
                "username": "swarmcore",
                "password": "swarmcore",
            },
        )
        _vault_write(
            address,
            headers,
            f"v1/{mount}/roles/{role}",
            {
                "db_name": "swarmcore",
                "default_ttl": "30s",
                "max_ttl": "60s",
                "creation_statements": (
                    "CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' "
                    "VALID UNTIL '{{expiration}}';"
                ),
                "revocation_statements": 'DROP ROLE IF EXISTS "{{name}}";',
            },
        )
        provider = VaultSecretProvider(address, token)
        async with provider.lease(f"secret://dynamic/{mount}/creds/{role}") as lease:
            username = lease.values["username"]
            password = lease.values["password"]
            connection = await asyncpg.connect(
                host="localhost",
                port=15432,
                database="swarmcore_test",
                user=username,
                password=password,
            )
            try:
                assert await connection.fetchval("SELECT 1") == 1
            finally:
                await connection.close()
        with pytest.raises(asyncpg.InvalidAuthorizationSpecificationError):
            await asyncpg.connect(
                host="localhost",
                port=15432,
                database="swarmcore_test",
                user=username,
                password=password,
            )
    finally:
        _vault_delete(address, headers, f"v1/sys/mounts/{mount}")


@pytest.mark.asyncio
async def test_model_gateway_releases_budget_on_provider_429_500_and_timeout(
    runtime_harness: RuntimeHarness,
) -> None:
    spec = sequential(
        "model-provider-faults",
        {"one": {"role": "worker", "instructions": "work"}},
    ).model_dump(mode="json", by_alias=True, exclude_none=True)
    created = runtime_harness.api.post(
        runtime_harness.project_url("runs"),
        headers={**runtime_harness.headers, "Idempotency-Key": uuid4().hex},
        json={"spec": spec, "input": {}},
    )
    assert created.status_code == 202
    run_id = created.json()["runId"]
    run_uuid = UUID(run_id)
    async with tenant_transaction(
        runtime_harness.database.sessions,
        tenant_id=runtime_harness.tenant_id,
        project_id=runtime_harness.project_id,
    ) as session:
        await session.execute(
            update(RunCommand)
            .where(RunCommand.run_id == run_uuid, RunCommand.status == "PENDING")
            .values(status="APPLIED")
        )
        await session.execute(
            update(OutboxEvent)
            .where(
                OutboxEvent.aggregate_id == run_uuid,
                OutboxEvent.destination == "temporal",
                OutboxEvent.status == "PENDING",
            )
            .values(status="DELIVERED")
        )
    secret = b"integration-model-capability-secret"
    issuer = ModelCapabilityIssuer(secret)

    with _mock_litellm() as (url, responses):
        settings = ModelGatewaySettings(
            database_url=runtime_harness.database_url,
            model_capability_secret=secret.decode(),
            litellm_url=url,
            litellm_timeout_seconds=0.1,
            telemetry_enabled=False,
        )
        with TestClient(create_model_gateway(settings), raise_server_exceptions=False) as client:
            replay_token = _model_token(issuer, runtime_harness, run_id)
            responses.put(
                (
                    200,
                    {
                        "id": "request-ok",
                        "model": "openai/gpt-4o-mini",
                        "choices": [
                            {
                                "index": 0,
                                "message": {"role": "assistant", "content": "ok"},
                                "finish_reason": "stop",
                            }
                        ],
                        "usage": {"prompt_tokens": 3, "completion_tokens": 2},
                        "response_cost": 0.01,
                    },
                    0.0,
                )
            )
            assert (
                _invoke_model(
                    client,
                    issuer,
                    runtime_harness,
                    run_id,
                    token=replay_token,
                ).status_code
                == 200
            )
            assert (
                _invoke_model(
                    client,
                    issuer,
                    runtime_harness,
                    run_id,
                    token=replay_token,
                ).status_code
                == 409
            )
            for status, delay in ((429, 0.0), (500, 0.0), (200, 0.3)):
                responses.put((status, {"error": "provider failure"}, delay))
                response = _invoke_model(client, issuer, runtime_harness, run_id)
                assert response.status_code == 500

    async with tenant_transaction(
        runtime_harness.database.sessions,
        tenant_id=runtime_harness.tenant_id,
        project_id=runtime_harness.project_id,
    ) as session:
        run = await session.get(Run, run_id)
        assert run is not None
        assert run.usage["reservedTokens"] == 0
        assert run.usage["tokens"] == 5
        usage_count = await session.scalar(
            select(func.count(ModelUsageRecord.id)).where(ModelUsageRecord.run_id == run.id)
        )
        assert usage_count == 1


@pytest.mark.asyncio
async def test_webhook_signature_and_persistent_retry(
    runtime_harness: RuntimeHarness,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "integration-webhook-signing-secret-at-least-32-bytes"
    secrets = InMemorySecretProvider({"secret://webhooks/integration": {"signingKey": secret}})
    delivery_id = uuid4()
    event_id = uuid4()
    endpoint_id = uuid4()
    run_id = uuid4()
    async with tenant_transaction(
        runtime_harness.database.sessions,
        tenant_id=runtime_harness.tenant_id,
        project_id=runtime_harness.project_id,
    ) as session:
        endpoint = WebhookEndpoint(
            id=endpoint_id,
            tenant_id=runtime_harness.tenant_id,
            project_id=runtime_harness.project_id,
            url="https://webhook.example.test/events",
            secret_ref="secret://webhooks/integration",
            event_types=["run.completed"],
        )
        session.add(endpoint)
        await session.flush()
        session.add(
            WebhookDelivery(
                id=delivery_id,
                tenant_id=runtime_harness.tenant_id,
                endpoint_id=endpoint_id,
                event_id=event_id,
                delivery_id=str(delivery_id),
                next_attempt_at=datetime.now(UTC),
            )
        )
        session.add(
            OutboxEvent(
                tenant_id=runtime_harness.tenant_id,
                aggregate_id=run_id,
                destination="webhook",
                partition_key=str(endpoint_id),
                source_id=delivery_id,
                type="run.completed",
                payload={
                    "projectId": str(runtime_harness.project_id),
                    "endpointId": str(endpoint_id),
                    "deliveryId": str(delivery_id),
                    "event": {"runId": str(run_id), "secret": "redact-me"},
                },
            )
        )

    responses = iter((500, 204))
    sent: list[tuple[bytes, str, str]] = []

    def post(
        url: str,
        body: bytes,
        signature: str,
        sent_delivery_id: str,
        allowed_hosts: frozenset[str],
    ) -> int:
        assert url == "https://webhook.example.test/events"
        assert allowed_hosts == frozenset({"webhook.example.test"})
        sent.append((body, signature, sent_delivery_id))
        return next(responses)

    monkeypatch.setattr("swarmcore_worker_webhook.worker._post_https", post)
    worker = WebhookWorker(
        runtime_harness.database.sessions,
        RolePolicyEngine(),
        secrets,
        worker_id="webhook-worker:integration",
        allowed_hosts=frozenset({"webhook.example.test"}),
    )
    assert await worker.run_once() == 1
    async with tenant_transaction(
        runtime_harness.database.sessions,
        tenant_id=runtime_harness.tenant_id,
        project_id=runtime_harness.project_id,
    ) as session:
        delivery = await session.get(WebhookDelivery, delivery_id)
        assert delivery is not None
        assert delivery.status == "PENDING"
        assert delivery.attempts == 1
        outbox = await session.scalar(
            select(OutboxEvent).where(OutboxEvent.source_id == delivery_id)
        )
        assert outbox is not None
        outbox.available_at = datetime.now(UTC)

    assert await worker.run_once() == 1
    assert len(sent) == 2
    body, signature, sent_delivery_id = sent[-1]
    document = json.loads(body)
    assert document["data"]["secret"] == "redact-me"
    WebhookSigner(secret.encode()).verify(
        WebhookEnvelope(
            delivery_id=document["deliveryId"],
            timestamp=document["timestamp"],
            event_type=document["type"],
            payload=document["data"],
        ),
        signature,
    )
    assert sent_delivery_id == str(delivery_id)
    async with tenant_transaction(
        runtime_harness.database.sessions,
        tenant_id=runtime_harness.tenant_id,
        project_id=runtime_harness.project_id,
    ) as session:
        delivery = await session.get(WebhookDelivery, delivery_id)
        assert delivery is not None
        assert delivery.status == "DELIVERED"
        assert delivery.attempts == 2
        outbox = await session.scalar(
            select(OutboxEvent).where(OutboxEvent.source_id == delivery_id)
        )
        assert outbox is not None
        assert outbox.status == "DELIVERED"
    assert len(secrets.revoked) == 2


class _LiteLlmHandler(BaseHTTPRequestHandler):
    response_queue: Queue[tuple[int, dict[str, Any], float]]

    def do_POST(self) -> None:
        self.rfile.read(int(self.headers.get("Content-Length", "0")))
        status, document, delay = self.response_queue.get(timeout=5)
        if delay:
            time.sleep(delay)
        body = json.dumps(document).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        with suppress(BrokenPipeError):
            self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        del format, args


@contextmanager
def _mock_litellm() -> Any:
    responses: Queue[tuple[int, dict[str, Any], float]] = Queue()
    handler = type("QueuedLiteLlmHandler", (_LiteLlmHandler,), {"response_queue": responses})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", responses
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def _invoke_model(
    client: TestClient,
    issuer: ModelCapabilityIssuer,
    harness: RuntimeHarness,
    run_id: str,
    *,
    token: str | None = None,
) -> Any:
    capability = token or _model_token(issuer, harness, run_id)
    return client.post(
        "/internal/v1/models:invoke",
        json={
            "capabilityToken": capability,
            "messages": [{"role": "user", "content": "hello"}],
            "maxTokens": 10,
        },
    )


def _model_token(
    issuer: ModelCapabilityIssuer, harness: RuntimeHarness, run_id: str
) -> str:
    return issuer.issue(
        tenant_id=str(harness.tenant_id),
        project_id=str(harness.project_id),
        run_id=run_id,
        task_execution_id=f"model-test-{uuid4()}",
        subject_id="agent-worker:integration",
        logical_model="model://general",
    )


def _vault_write(
    address: str, headers: dict[str, str], path: str, document: dict[str, Any]
) -> dict[str, Any]:
    request = Request(
        f"{address.rstrip('/')}/{path}",
        data=json.dumps(document).encode(),
        headers=headers,
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        if response.status == 204:
            return {}
        return cast(dict[str, Any], json.loads(response.read()))


def _vault_delete(address: str, headers: dict[str, str], path: str) -> None:
    request = Request(f"{address.rstrip('/')}/{path}", headers=headers, method="DELETE")
    with urlopen(request, timeout=10):
        pass
