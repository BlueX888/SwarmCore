from __future__ import annotations

import hashlib
import json
import logging
import ssl
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from swarmcore_api import create_app
from swarmcore_api.authentication import AuthenticationError, _identity_from_claims
from swarmcore_api.settings import Settings
from swarmcore_governance import (
    InMemorySecretProvider,
    ModelCapabilityIssuer,
    PolicyDecision,
    PolicyObligations,
    SandboxAdmission,
    SandboxRequest,
    SandboxViolation,
    WorkloadTls,
)
from swarmcore_model_gateway.main import Settings as ModelGatewaySettings
from swarmcore_model_gateway.main import create_app as create_model_gateway
from swarmcore_observability import JsonRedactingFormatter
from swarmcore_registry import RegistrySnapshot, builtin_registry
from swarmcore_sandbox_manager.main import _manifest, _network_policy, _sandbox_status
from swarmcore_tool_gateway import (
    CapabilityTokenIssuer,
    GatewayError,
    InMemoryEffectJournal,
    ToolGateway,
    ToolInvocation,
)

from .test_spec import VALID_SPEC


def test_jwt_identity_requires_and_enforces_project_scopes() -> None:
    project = "00000000-0000-0000-0000-000000000002"
    other = "00000000-0000-0000-0000-000000000003"
    claims = {
        "sub": "operator-1",
        "tenant_id": "00000000-0000-0000-0000-000000000001",
        "roles": ["run_operator"],
        "scopes": [],
        "project_scopes": {project: ["artifact.read"]},
        "iss": "https://id.example.test",
        "aud": "swarmcore-api",
    }
    identity = _identity_from_claims(claims)
    assert identity.can_access_project(UUID(project))
    assert not identity.can_access_project(UUID(other))
    assert identity.scopes_for(UUID(project)) == ("artifact.read",)

    with pytest.raises(AuthenticationError, match="project scopes"):
        _identity_from_claims({**claims, "project_scopes": None})


def test_m4_migration_has_rls_append_only_audit_and_governance_tables() -> None:
    migration = Path("packages/persistence/alembic/versions/0006_m4_governance.py").read_text(
        encoding="utf-8"
    )
    assert 'down_revision: str | None = "0005_m3_tool_effect_lease"' in migration
    for table in (
        "artifacts",
        "artifact_download_grants",
        "audit_logs",
        "model_usage_records",
        "webhook_endpoints",
        "webhook_deliveries",
        "sandbox_executions",
        "compensation_records",
    ):
        assert f'"{table}"' in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "FORCE ROW LEVEL SECURITY" in migration
    assert "audit_logs_append_only" in migration


def test_rest_policy_denies_missing_or_insufficient_identity() -> None:
    import yaml

    project = "00000000-0000-0000-0000-000000000002"
    path = f"/v1/projects/{project}/strategies/compile"
    with TestClient(create_app(Settings())) as client:
        missing = client.post(path, json={"spec": yaml.safe_load(VALID_SPEC)})
        denied = client.post(
            path,
            headers={
                "X-Tenant-ID": "00000000-0000-0000-0000-000000000001",
                "X-Roles": "viewer",
            },
            json={"spec": yaml.safe_load(VALID_SPEC)},
        )
    assert missing.status_code == 401
    assert denied.status_code == 403
    assert denied.json()["detail"] == "POLICY_DENIED"


def test_model_gateway_openai_route_requires_matching_run_capability() -> None:
    secret = "m4-model-gateway-capability-secret"
    token = ModelCapabilityIssuer(secret.encode()).issue(
        tenant_id="00000000-0000-0000-0000-000000000001",
        project_id="00000000-0000-0000-0000-000000000002",
        run_id="00000000-0000-0000-0000-000000000003",
        task_execution_id="task-1",
        subject_id="agent-worker:test",
        logical_model="model://general",
    )
    app = create_model_gateway(ModelGatewaySettings(model_capability_secret=secret))
    with TestClient(app) as client:
        missing = client.post(
            "/v1/chat/completions",
            json={"model": "model://general", "messages": []},
        )
        mismatched = client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {token}"},
            json={"model": "model://other", "messages": []},
        )
    assert missing.status_code == 401
    assert mismatched.status_code == 403


@pytest.mark.asyncio
async def test_gateway_secret_is_leased_redacted_and_revoked() -> None:
    secret_provider = InMemorySecretProvider(
        {"secret://mail/provider": {"apiKey": "lease-only-secret"}}
    )
    issuer = CapabilityTokenIssuer("m4-security-contract-capability-secret")
    observed: list[dict[str, Any]] = []

    async def search(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
        del effect_id
        observed.append(input_value)
        return {"items": [{"authenticated": bool(input_value["auth"]["apiKey"])}]}

    base_registry = builtin_registry()
    search_registration = base_registry.resolve_tool("tool://search@1")
    assert search_registration is not None
    registry = RegistrySnapshot.create(
        tools=(
            search_registration.model_copy(
                update={
                    "input_schema": {
                        "type": "object",
                        "required": ["query", "auth"],
                        "properties": {
                            "query": {"type": "string"},
                            "auth": {"type": "object"},
                        },
                        "additionalProperties": False,
                    }
                }
            ),
        )
    )

    gateway = ToolGateway(
        registry,
        issuer,
        InMemoryEffectJournal(),
        {"builtin.search": search},
        secrets=secret_provider,
    )
    token = issuer.issue(
        tenant_id="tenant-1",
        project_id="project-1",
        run_id="run-1",
        node_key="search",
        tool_ref="tool://search@1",
        execution_id="execution-1",
        effect_id="effect-1",
        approved=False,
    )
    output = await gateway.invoke(
        ToolInvocation(
            token=token,
            effectId="effect-1",
            input={
                "query": "swarm",
                "auth": {"secretRef": "secret://mail/provider"},
            },
        )
    )
    assert output["content"]["items"][0]["authenticated"] is True
    assert observed[0]["auth"]["apiKey"] == "lease-only-secret"
    assert secret_provider.revoked == {"memory/1"}


@pytest.mark.asyncio
async def test_approved_capability_is_bound_to_canonical_input_hash() -> None:
    issuer = CapabilityTokenIssuer("m4-input-binding-capability-secret")
    expected_hash = hashlib.sha256(b'{"reports":{}}').hexdigest()
    token = issuer.issue(
        tenant_id="tenant-1",
        project_id="project-1",
        run_id="run-1",
        node_key="publish",
        tool_ref="tool://publish-report@1",
        execution_id="execution-1",
        effect_id="effect-1",
        approved=True,
        canonical_input_hash=expected_hash,
        policy_revision="policy:v1",
    )
    gateway = ToolGateway(builtin_registry(), issuer, InMemoryEffectJournal(), executors={})
    with pytest.raises(GatewayError, match="input hash"):
        await gateway.invoke(
            ToolInvocation(
                token=token,
                effectId="effect-1",
                input={"reports": {"changed": True}},
            )
        )


def test_json_logger_redacts_sensitive_structured_fields() -> None:
    record = logging.LogRecord(
        "service",
        logging.INFO,
        "",
        0,
        "authorization: Bearer raw-token password=hunter2",
        (),
        None,
    )
    record.fields = {"token": "secret", "nested": {"password": "secret", "ok": 1}}
    payload = json.loads(JsonRedactingFormatter().format(record))
    assert payload["fields"] == {
        "token": "[REDACTED]",
        "nested": {"password": "[REDACTED]", "ok": 1},
    }
    assert "raw-token" not in payload["message"]
    assert "hunter2" not in payload["message"]


def test_sandbox_manifest_and_network_policy_enforce_isolation() -> None:
    image = "registry.example/sandbox@sha256:" + "a" * 64
    request = SandboxRequest(
        image=image,
        command=("/bin/task",),
        cpu_millis=500,
        memory_mib=256,
        workspace_mib=128,
        timeout_seconds=30,
        network_targets=("1.1.1.1:443",),
    )
    decision = PolicyDecision(
        allow=True,
        policy_revision="test:v1",
        obligations=PolicyObligations(
            max_duration_seconds=60,
            allowed_egress=("1.1.1.1:443",),
        ),
    )
    admitted = SandboxAdmission(allowed_images=frozenset({image})).admit(request, decision)
    manifest = _manifest(admitted.request, execution_id="execution-1", namespace="test")
    pod = manifest["spec"]["template"]["spec"]
    container = pod["containers"][0]
    assert pod["runtimeClassName"] == "gvisor"
    assert pod["automountServiceAccountToken"] is False
    assert pod["securityContext"]["runAsNonRoot"] is True
    assert container["securityContext"]["allowPrivilegeEscalation"] is False
    assert container["securityContext"]["readOnlyRootFilesystem"] is True
    assert container["securityContext"]["capabilities"] == {"drop": ["ALL"]}

    network = _network_policy(admitted.request, execution_id="execution-1", namespace="test")
    assert network["spec"]["policyTypes"] == ["Ingress", "Egress"]
    assert network["spec"]["ingress"] == []
    assert network["spec"]["egress"] == [
        {
            "to": [{"ipBlock": {"cidr": "1.1.1.1/32"}}],
            "ports": [{"protocol": "TCP", "port": 443}],
        }
    ]


@pytest.mark.parametrize("target", ["api.example.test:443", "169.254.169.254:80"])
def test_sandbox_rejects_unenforceable_or_private_egress(target: str) -> None:
    image = "registry.example/sandbox@sha256:" + "a" * 64
    request = SandboxRequest(
        image=image,
        command=("/bin/task",),
        cpu_millis=500,
        memory_mib=256,
        workspace_mib=128,
        timeout_seconds=30,
        network_targets=(target,),
    )
    decision = PolicyDecision(
        allow=True,
        policy_revision="test:v1",
        obligations=PolicyObligations(
            max_duration_seconds=60,
            allowed_egress=(target,),
        ),
    )
    with pytest.raises(SandboxViolation):
        SandboxAdmission(allowed_images=frozenset({image})).admit(request, decision)


def test_sandbox_node_loss_is_reconciled_as_retryable_failure() -> None:
    status = _sandbox_status(
        {"status": {"active": 1}},
        {"items": [{"status": {"phase": "Failed", "reason": "NodeLost"}}]},
    )
    assert status == {"status": "FAILED", "reason": "NodeLost", "retryable": True}


def test_workload_mtls_is_complete_and_required_in_production(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="requires CA"):
        WorkloadTls(ca_file="ca.pem").validate()
    with pytest.raises(ValueError, match="production mode"):
        ModelGatewaySettings(deployment_mode="production")

    ca = tmp_path / "ca.pem"
    cert = tmp_path / "workload.pem"
    key = tmp_path / "workload-key.pem"
    for path in (ca, cert, key):
        path.write_text("test fixture", encoding="utf-8")
    tls = WorkloadTls(str(ca), str(cert), str(key)).validate(required=True)
    assert tls.uvicorn_options()["ssl_cert_reqs"] == ssl.CERT_REQUIRED
