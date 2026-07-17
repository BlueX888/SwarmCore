from __future__ import annotations

from pathlib import Path
from socketserver import BaseRequestHandler, ThreadingTCPServer
from threading import Thread
from typing import Any

import pytest
from swarmcore_governance import (
    ArtifactCapabilityIssuer,
    ArtifactError,
    ArtifactGateway,
    BudgetExceeded,
    BudgetLimits,
    BudgetManager,
    ClamAvScanner,
    CompensationEntry,
    CompensationManager,
    InMemoryAuditWriter,
    InMemorySecretProvider,
    LocalArtifactStore,
    ModelCapabilityIssuer,
    ModelGateway,
    ModelResponse,
    ModelUsage,
    PolicyDecision,
    PolicyDenied,
    PolicyError,
    PolicyRequest,
    PolicySubject,
    RolePolicyEngine,
    S3ArtifactStore,
    SandboxAdmission,
    SandboxCapabilityIssuer,
    SandboxRequest,
    SandboxViolation,
    SecretError,
    SecretScanner,
    VaultSecretProvider,
    WebhookEnvelope,
    WebhookError,
    WebhookSigner,
)
from swarmcore_governance.policy import OpaPolicyEngine


def policy_request(action: str, *, roles: tuple[str, ...] = ("workload",)) -> PolicyRequest:
    return PolicyRequest(
        subject=PolicySubject(id="worker-1", tenantId="tenant-1", roles=roles),
        action=action,
        resource={"projectId": "project-1"},
    )


@pytest.mark.asyncio
async def test_role_policy_applies_approval_and_emergency_deny() -> None:
    engine = RolePolicyEngine(emergency_denies=frozenset({"secret.read"}))
    tool = policy_request("tool.execute").model_copy(
        update={"resource": {"projectId": "project-1", "risk": "HIGH"}}
    )
    decision = await engine.evaluate(tool)
    assert decision.allow
    assert decision.obligations.require_approval

    denied = await engine.evaluate(policy_request("secret.read"))
    with pytest.raises(PolicyDenied, match="emergency"):
        denied.enforce()


@pytest.mark.asyncio
async def test_opa_fail_closed_and_rejects_unknown_obligation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = OpaPolicyEngine("http://opa.test/v1/data/swarmcore/decision")

    monkeypatch.setattr(
        engine,
        "_post",
        lambda _: b'{"result":{"allow":true,"obligations":{"shell":true},"policyRevision":"p1"}}',
    )
    with pytest.raises(PolicyError, match="OPA decision failed"):
        await engine.evaluate(policy_request("run.read"))

    monkeypatch.setattr(engine, "_post", lambda _: (_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(PolicyError, match="TimeoutError"):
        await engine.evaluate(policy_request("run.read"))


@pytest.mark.asyncio
async def test_secret_lease_is_revoked_and_scanner_blocks_leak() -> None:
    provider = InMemorySecretProvider({"secret://tools/mail": {"token": "secret-value"}})
    async with provider.lease("secret://tools/mail") as lease:
        lease_id = lease.lease_id
        scanner = SecretScanner(lease.values)
        assert scanner.redact("token=secret-value") == "token=[REDACTED]"
        with pytest.raises(SecretError, match="leased secret"):
            scanner.assert_clean(b"payload secret-value")
    assert lease_id in provider.revoked


@pytest.mark.asyncio
async def test_vault_dynamic_secret_revokes_real_lease() -> None:
    class FakeVault(VaultSecretProvider):
        def __init__(self) -> None:
            super().__init__("http://vault", "workload-token")
            self.requested: list[str] = []
            self.revoked: list[str] = []

        def _request(self, path: str, token: str | None = None) -> dict[str, Any]:
            assert token == "workload-token"
            self.requested.append(path)
            return {
                "data": {"username": "short-lived", "password": "credential"},
                "lease_id": "database/creds/readonly/lease-1",
                "lease_duration": 30,
            }

        def _revoke(self, lease_id: str, token: str | None = None) -> None:
            assert token == "workload-token"
            self.revoked.append(lease_id)

    provider = FakeVault()
    async with provider.lease("secret://dynamic/database/creds/readonly") as lease:
        assert lease.ttl_seconds == 30
        assert lease.values["username"] == "short-lived"
    assert provider.requested == ["v1/database/creds/readonly"]
    assert provider.revoked == ["database/creds/readonly/lease-1"]


@pytest.mark.asyncio
async def test_vault_kubernetes_auth_uses_service_account_and_revokes_token(
    tmp_path: Path,
) -> None:
    jwt_path = tmp_path / "token"
    jwt_path.write_text("signed-service-account-jwt", encoding="utf-8")

    class FakeVault(VaultSecretProvider):
        def __init__(self) -> None:
            super().__init__(
                "http://vault",
                kubernetes_role="worker-tool",
                kubernetes_jwt_path=str(jwt_path),
            )
            self.logins: list[str] = []
            self.request_tokens: list[str | None] = []
            self.revoked_tokens: list[str] = []

        def _login(self, jwt: str) -> dict[str, Any]:
            self.logins.append(jwt)
            return {"auth": {"client_token": "short-vault-token"}}

        def _request(self, path: str, token: str | None = None) -> dict[str, Any]:
            assert path == "v1/secret/data/tools/mail"
            self.request_tokens.append(token)
            return {"data": {"data": {"apiKey": "leased-value"}}}

        def _revoke_token(self, token: str) -> None:
            self.revoked_tokens.append(token)

    provider = FakeVault()
    async with provider.lease("secret://tools/mail") as lease:
        assert lease.values["apiKey"] == "leased-value"
    assert provider.logins == ["signed-service-account-jwt"]
    assert provider.request_tokens == ["short-vault-token"]
    assert provider.revoked_tokens == ["short-vault-token"]


@pytest.mark.asyncio
async def test_artifact_gateway_scopes_integrity_and_one_time_download(tmp_path: Path) -> None:
    audit = InMemoryAuditWriter()
    gateway = ArtifactGateway(
        LocalArtifactStore(tmp_path),
        RolePolicyEngine(),
        audit,
        b"a" * 32,
        max_artifact_bytes=100,
        max_run_bytes=120,
    )
    upload_request = policy_request("artifact.write")
    ref = await gateway.upload(
        upload_request,
        run_id="run-1",
        filename="result.json",
        media_type="application/json",
        kind="result",
        content=b'{"ok":true}',
    )
    assert ref.status == "AVAILABLE"
    assert not (tmp_path / "tenant-1" / "project-1" / "run-1" / ref.id / "v1").name.startswith(
        ".staging"
    )

    token = await gateway.issue_download(policy_request("artifact.read"), ref.id)
    downloaded, content = await gateway.download(token)
    assert downloaded == ref
    assert content == b'{"ok":true}'
    with pytest.raises(ArtifactError, match="already consumed"):
        await gateway.download(token)

    other_tenant = PolicyRequest(
        subject=PolicySubject(id="worker-2", tenantId="tenant-2", roles=("workload",)),
        action="artifact.read",
        resource={"projectId": "project-1"},
    )
    with pytest.raises(ArtifactError, match="not found"):
        await gateway.issue_download(other_tenant, ref.id)
    assert len(audit.export(tenant_id="tenant-1", project_id="project-1")) == 2


class _Body:
    def __init__(self, content: bytes) -> None:
        self._content = content

    def read(self) -> bytes:
        return self._content


class _S3:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deleted: list[str] = []
        self.put_calls: list[dict[str, object]] = []
        self.copy_calls: list[dict[str, object]] = []

    def put_object(self, **kwargs: object) -> object:
        self.put_calls.append(kwargs)
        self.objects[str(kwargs["Key"])] = bytes(kwargs["Body"])
        return {}

    def copy_object(self, **kwargs: object) -> object:
        self.copy_calls.append(kwargs)
        source = kwargs["CopySource"]
        assert isinstance(source, dict)
        self.objects[str(kwargs["Key"])] = self.objects[str(source["Key"])]
        return {}

    def get_object(self, **kwargs: object) -> dict[str, object]:
        return {"Body": _Body(self.objects[str(kwargs["Key"])])}

    def delete_object(self, **kwargs: object) -> object:
        key = str(kwargs["Key"])
        self.deleted.append(key)
        self.objects.pop(key, None)
        return {}


@pytest.mark.asyncio
async def test_s3_store_promotes_staging_and_cleans_it() -> None:
    client = _S3()
    store = S3ArtifactStore(client, "bucket", kms_key_id="kms-key-1")
    await store.put("tenant/project/artifact/v1", b"content")
    assert await store.get("tenant/project/artifact/v1") == b"content"
    assert len(client.deleted) == 1
    assert client.deleted[0].startswith("tenant/staging/")
    assert all(not key.startswith("tenant/staging/") for key in client.objects)
    for call in [client.put_calls[0], client.copy_calls[0]]:
        assert call["ServerSideEncryption"] == "aws:kms"
        assert call["SSEKMSKeyId"] == "kms-key-1"
        assert call["SSEKMSEncryptionContext"] == '{"tenantId":"tenant"}'


@pytest.mark.asyncio
async def test_clamav_stream_rejection_blocks_artifact() -> None:
    class MalwareHandler(BaseRequestHandler):
        def handle(self) -> None:
            request = self.request
            received = b""
            while not received.endswith(b"\0\0\0\0"):
                received += request.recv(4096)
            request.sendall(b"stream: Eicar-Test-Signature FOUND\0")

    server = ThreadingTCPServer(("127.0.0.1", 0), MalwareHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        scanner = ClamAvScanner("127.0.0.1", server.server_address[1])
        with pytest.raises(ArtifactError, match="malware scan"):
            await scanner.scan(b"EICAR integration fixture")
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def test_artifact_and_model_capabilities_are_narrowly_scoped() -> None:
    artifact_tokens = ArtifactCapabilityIssuer(b"a" * 32)
    artifact = artifact_tokens.issue(
        action="artifact.write",
        tenant_id="tenant-1",
        project_id="project-1",
        run_id="run-1",
        subject_id="worker-1",
        artifact_id="artifact-1",
    )
    assert artifact_tokens.verify(artifact).artifact_id == "artifact-1"

    model_tokens = ModelCapabilityIssuer(b"m" * 32)
    model = model_tokens.issue(
        tenant_id="tenant-1",
        project_id="project-1",
        run_id="run-1",
        task_execution_id="task-1",
        subject_id="worker-1",
        logical_model="model://general",
    )
    assert model_tokens.verify(model).logical_model == "model://general"


class _ModelAdapter:
    async def invoke(
        self, *, model: str, messages: list[dict[str, str]], max_tokens: int
    ) -> ModelResponse:
        del messages, max_tokens
        return ModelResponse(
            content="ok",
            usage=ModelUsage(60, 25, 0.9, model, "provider", "price:v1"),
        )


@pytest.mark.asyncio
async def test_model_gateway_reserves_and_enforces_budget() -> None:
    budgets = BudgetManager()
    await budgets.create("run-1", BudgetLimits(max_tokens=100, max_cost_usd=1))
    gateway = ModelGateway(
        {"provider": _ModelAdapter()},
        {"model://general": ("provider", "real-model")},
        budgets,
        RolePolicyEngine(),
    )
    response, event = await gateway.invoke(
        policy_request("model.invoke"),
        run_id="run-1",
        logical_model="model://general",
        messages=[{"role": "user", "content": "hello"}],
        max_tokens=90,
    )
    assert response.content == "ok"
    assert event == "budget.warning"
    assert budgets.snapshot("run-1")["tokens"] == 85
    with pytest.raises(BudgetExceeded, match="fail"):
        await budgets.reserve("run-1", 20)


def test_webhook_signing_replay_window() -> None:
    signer = WebhookSigner(b"w" * 32)
    envelope = WebhookEnvelope("delivery-1", 1_000, "run.completed", {"runId": "r1"})
    signature = signer.sign(envelope)
    signer.verify(envelope, signature, now=1_001)
    with pytest.raises(WebhookError, match="replay window"):
        signer.verify(envelope, signature, now=1_301)


def test_sandbox_admission_rejects_privilege_and_private_egress() -> None:
    admission = SandboxAdmission(
        allowed_images=frozenset({"registry.example/sandbox@sha256:" + "a" * 64})
    )
    decision = PolicyDecision(
        allow=True,
        obligations={"maxDurationSeconds": 60, "allowedEgress": ["1.1.1.1:443"]},
        policyRevision="p1",
    )
    request = SandboxRequest(
        image="registry.example/sandbox@sha256:" + "a" * 64,
        command=("python", "main.py"),
        cpu_millis=500,
        memory_mib=256,
        workspace_mib=100,
        timeout_seconds=30,
        network_targets=("1.1.1.1:443",),
    )
    job = admission.admit(request, decision)
    assert job.runtime_class == "gvisor"
    assert not job.automount_service_account_token
    with pytest.raises(SandboxViolation, match="privileged"):
        admission.admit(SandboxRequest(**{**request.__dict__, "privileged": True}), decision)

    private = decision.model_copy(
        update={
            "obligations": decision.obligations.model_copy(
                update={"allowed_egress": ("169.254.169.254:80",)}
            )
        }
    )
    with pytest.raises(SandboxViolation, match="private or metadata"):
        admission.admit(
            SandboxRequest(**{**request.__dict__, "network_targets": ("169.254.169.254:80",)}),
            private,
        )


def test_sandbox_capability_is_scoped_and_tamper_evident() -> None:
    issuer = SandboxCapabilityIssuer(b"s" * 32)
    token = issuer.issue(
        tenant_id="tenant-1",
        project_id="project-1",
        run_id="run-1",
        task_execution_id="task-1",
        subject_id="worker-1",
    )
    capability = issuer.verify(token)
    assert capability.run_id == "run-1"
    with pytest.raises(SandboxViolation, match="invalid"):
        issuer.verify(token[:-1] + ("a" if token[-1] != "a" else "b"))


@pytest.mark.asyncio
async def test_compensation_is_reverse_order_and_idempotent() -> None:
    called: list[str] = []

    async def compensate(value: dict[str, Any]) -> None:
        called.append(str(value["value"]))

    manager = CompensationManager({"undo": compensate})
    entries = [
        CompensationEntry("e1", "undo", {"value": "first"}),
        CompensationEntry("e2", "undo", {"value": "second"}),
        CompensationEntry("e3", "manual", {}),
    ]
    result = await manager.compensate(entries)
    assert [item.status for item in result] == [
        "MANUAL_RECOVERY_REQUIRED",
        "COMPENSATED",
        "COMPENSATED",
    ]
    assert called == ["second", "first"]
    repeated = await manager.compensate(entries[:2])
    assert all(item.status == "ALREADY_COMPENSATED" for item in repeated)
