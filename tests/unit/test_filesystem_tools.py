from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from jsonschema import Draft202012Validator
from swarmcore_registry import ToolRisk, builtin_registry
from swarmcore_tool_gateway import (
    AuditEvent,
    CapabilityTokenIssuer,
    FilesystemErrorCode,
    FilesystemExecutorMode,
    FilesystemToolConfig,
    FilesystemToolError,
    GatewayError,
    InMemoryEffectJournal,
    ToolGateway,
    ToolInvocation,
    assemble_tool_executors,
    builtin_executors,
    filesystem_executors,
)
from swarmcore_tool_gateway.filesystem.paths import SafePathResolver
from swarmcore_tool_gateway.filesystem.sandbox import FilesystemSandboxTask

FILESYSTEM_OPERATIONS = {
    "filesystem.read_text",
    "filesystem.write_text",
    "filesystem.list",
    "filesystem.stat",
}

FILESYSTEM_REFS = {
    "tool://filesystem/read-text@1",
    "tool://filesystem/write-text@1",
    "tool://filesystem/list@1",
    "tool://filesystem/stat@1",
}


class RecordingAudit:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def record(self, event: AuditEvent) -> None:
        self.events.append(event)


class FailingSandboxTransport:
    async def available(self) -> bool:
        return False

    async def execute(self, task: FilesystemSandboxTask) -> dict[str, Any]:
        del task
        raise FilesystemToolError(
            FilesystemErrorCode.SANDBOX_UNAVAILABLE,
            "sandbox filesystem execution did not return a declared result",
        )


def _config(tmp_path: Path, **overrides: Any) -> FilesystemToolConfig:
    values: dict[str, Any] = {
        "enabled": True,
        "root": tmp_path,
        "allowed_mounts": frozenset({"workspace"}),
        "mode": FilesystemExecutorMode.LOCAL,
        "deployment_mode": "local",
        "max_read_bytes": 1024,
        "max_write_bytes": 1024,
        "max_list_entries": 100,
    }
    values.update(overrides)
    config = FilesystemToolConfig(**values)
    config.validate()
    return config


def _gateway(
    tmp_path: Path, *, audit: RecordingAudit | None = None
) -> tuple[ToolGateway, CapabilityTokenIssuer, RecordingAudit]:
    issuer = CapabilityTokenIssuer("development-only-capability-secret-32-bytes!!")
    sink = audit or RecordingAudit()
    gateway = ToolGateway(
        builtin_registry(),
        issuer,
        InMemoryEffectJournal(),
        assemble_tool_executors(filesystem=_config(tmp_path)),
        sink,
    )
    return gateway, issuer, sink


def _token(
    issuer: CapabilityTokenIssuer,
    *,
    tool_ref: str,
    tenant_id: str,
    project_id: str,
    effect_id: str,
    approved: bool,
    input_value: dict[str, Any],
) -> str:
    canonical = json.dumps(input_value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return issuer.issue(
        tenant_id=tenant_id,
        project_id=project_id,
        run_id=str(uuid4()),
        node_key="fs-1",
        tool_ref=tool_ref,
        execution_id=str(uuid4()),
        effect_id=effect_id,
        approved=approved,
        canonical_input_hash=hashlib.sha256(canonical.encode()).hexdigest() if approved else None,
    )


@pytest.mark.asyncio
async def test_registry_filesystem_tools_have_closed_contracts() -> None:
    tools = {item.ref: item for item in builtin_registry().tools if item.ref in FILESYSTEM_REFS}
    assert set(tools) == FILESYSTEM_REFS
    expectations = {
        "tool://filesystem/read-text@1": (ToolRisk.MEDIUM, "filesystem.read_text", False, True),
        "tool://filesystem/write-text@1": (ToolRisk.HIGH, "filesystem.write_text", True, True),
        "tool://filesystem/list@1": (ToolRisk.MEDIUM, "filesystem.list", False, True),
        "tool://filesystem/stat@1": (ToolRisk.MEDIUM, "filesystem.stat", False, True),
    }
    for ref, (risk, operation, side_effecting, idempotent) in expectations.items():
        tool = tools[ref]
        assert tool.operation == operation
        assert tool.risk is risk
        assert tool.side_effecting is side_effecting
        assert tool.idempotent is idempotent
        assert tool.recovery_policy == "idempotent"
        Draft202012Validator.check_schema(tool.input_schema)
        Draft202012Validator.check_schema(tool.output_schema)
        assert tool.input_schema["additionalProperties"] is False
        assert tool.output_schema["additionalProperties"] is False


def test_filesystem_factory_registers_all_operations(tmp_path: Path) -> None:
    executors = filesystem_executors(_config(tmp_path))
    assert set(executors) == FILESYSTEM_OPERATIONS
    assembled = assemble_tool_executors(filesystem=_config(tmp_path), extra={"x.custom": object()})
    assert FILESYSTEM_OPERATIONS.issubset(assembled)
    assert set(builtin_executors()).issubset(assembled)
    assert "x.custom" in assembled


@pytest.mark.asyncio
async def test_readiness_reports_unhealthy_when_disabled(tmp_path: Path) -> None:
    gateway = ToolGateway(
        builtin_registry(),
        CapabilityTokenIssuer("development-only-capability-secret-32-bytes!!"),
        InMemoryEffectJournal(),
        assemble_tool_executors(
            filesystem=_config(tmp_path, enabled=False, mode=FilesystemExecutorMode.DISABLED)
        ),
    )
    rows = {row["ref"]: row for row in await gateway.readiness()}
    for ref in FILESYSTEM_REFS:
        assert rows[ref]["executorRegistered"] is True
        assert rows[ref]["healthy"] is False


@pytest.mark.asyncio
async def test_tenant_and_project_isolation(tmp_path: Path) -> None:
    gateway, issuer, _ = _gateway(tmp_path)
    tenant_a = str(uuid4())
    tenant_b = str(uuid4())
    project_a = str(uuid4())
    project_b = str(uuid4())
    write_input = {
        "mount": "workspace",
        "path": "notes/hello.txt",
        "content": "tenant-a",
        "mode": "create",
    }
    write_token = _token(
        issuer,
        tool_ref="tool://filesystem/write-text@1",
        tenant_id=tenant_a,
        project_id=project_a,
        effect_id="write-1",
        approved=True,
        input_value=write_input,
    )
    await gateway.invoke(ToolInvocation(token=write_token, effectId="write-1", input=write_input))

    read_input = {"mount": "workspace", "path": "notes/hello.txt"}
    other_token = _token(
        issuer,
        tool_ref="tool://filesystem/read-text@1",
        tenant_id=tenant_b,
        project_id=project_b,
        effect_id="read-1",
        approved=False,
        input_value=read_input,
    )
    with pytest.raises(FilesystemToolError, match="FILESYSTEM_NOT_FOUND"):
        await gateway.invoke(ToolInvocation(token=other_token, effectId="read-1", input=read_input))

    same_tenant_other_project = _token(
        issuer,
        tool_ref="tool://filesystem/read-text@1",
        tenant_id=tenant_a,
        project_id=project_b,
        effect_id="read-2",
        approved=False,
        input_value=read_input,
    )
    with pytest.raises(FilesystemToolError, match="FILESYSTEM_NOT_FOUND"):
        await gateway.invoke(
            ToolInvocation(token=same_tenant_other_project, effectId="read-2", input=read_input)
        )


def test_path_escape_and_absolute_paths_are_rejected(tmp_path: Path) -> None:
    resolver = SafePathResolver(
        root=tmp_path,
        allowed_mounts=frozenset({"workspace"}),
        deny_names=frozenset({".env", ".git"}),
    )
    tenant = str(uuid4())
    project = str(uuid4())
    for bad in (
        "../secret.txt",
        "/etc/passwd",
        "C:\\Windows\\system32",
        "\\\\server\\share",
        "//server/share",
        "notes/\x00evil",
    ):
        with pytest.raises(FilesystemToolError, match="FILESYSTEM_PATH_INVALID"):
            resolver.resolve(
                tenant_id=tenant,
                project_id=project,
                mount="workspace",
                relative_path=bad,
            )


def test_sibling_prefix_bypass_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    resolver = SafePathResolver(
        root=root,
        allowed_mounts=frozenset({"workspace"}),
        deny_names=frozenset(),
    )
    tenant = str(uuid4())
    project = str(uuid4())
    jail = resolver.project_root(tenant_id=tenant, project_id=project) / "workspace"
    jail.mkdir(parents=True)
    sibling = Path(str(jail) + "-evil")
    sibling.mkdir()
    (sibling / "leak.txt").write_text("nope", encoding="utf-8")
    with pytest.raises(FilesystemToolError):
        resolver.resolve(
            tenant_id=tenant,
            project_id=project,
            mount="workspace",
            relative_path="../workspace-evil/leak.txt",
        )


@pytest.mark.asyncio
async def test_symlink_is_rejected(tmp_path: Path) -> None:
    gateway, issuer, _ = _gateway(tmp_path)
    tenant = str(uuid4())
    project = str(uuid4())
    write_input = {
        "mount": "workspace",
        "path": "real.txt",
        "content": "safe",
        "mode": "create",
    }
    token = _token(
        issuer,
        tool_ref="tool://filesystem/write-text@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="write-symlink",
        approved=True,
        input_value=write_input,
    )
    await gateway.invoke(ToolInvocation(token=token, effectId="write-symlink", input=write_input))
    config = _config(tmp_path)
    resolver = SafePathResolver(
        root=config.root,
        allowed_mounts=config.allowed_mounts,
        deny_names=config.deny_names,
    )
    target = resolver.resolve(
        tenant_id=tenant,
        project_id=project,
        mount="workspace",
        relative_path="real.txt",
    ).absolute_path
    link = target.parent / "link.txt"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation is not permitted in this environment")
    read_input = {"mount": "workspace", "path": "link.txt"}
    read_token = _token(
        issuer,
        tool_ref="tool://filesystem/read-text@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="read-link",
        approved=False,
        input_value=read_input,
    )
    with pytest.raises(FilesystemToolError, match="FILESYSTEM_LINK_REJECTED"):
        await gateway.invoke(
            ToolInvocation(token=read_token, effectId="read-link", input=read_input)
        )


@pytest.mark.asyncio
async def test_sensitive_paths_size_encoding_and_hash(tmp_path: Path) -> None:
    gateway, issuer, audit = _gateway(tmp_path)
    tenant = str(uuid4())
    project = str(uuid4())
    denied = {"mount": "workspace", "path": ".env", "content": "SECRET=1", "mode": "create"}
    denied_token = _token(
        issuer,
        tool_ref="tool://filesystem/write-text@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="deny-env",
        approved=True,
        input_value=denied,
    )
    with pytest.raises(FilesystemToolError, match="FILESYSTEM_PATH_DENIED"):
        await gateway.invoke(ToolInvocation(token=denied_token, effectId="deny-env", input=denied))

    large = {"mount": "workspace", "path": "big.txt", "content": "x" * 2048, "mode": "create"}
    large_token = _token(
        issuer,
        tool_ref="tool://filesystem/write-text@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="too-large",
        approved=True,
        input_value=large,
    )
    with pytest.raises(FilesystemToolError, match="FILESYSTEM_TOO_LARGE"):
        await gateway.invoke(ToolInvocation(token=large_token, effectId="too-large", input=large))

    write_input = {
        "mount": "workspace",
        "path": "notes/hello.txt",
        "content": "hello",
        "mode": "create",
    }
    write_token = _token(
        issuer,
        tool_ref="tool://filesystem/write-text@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="write-ok",
        approved=True,
        input_value=write_input,
    )
    written = await gateway.invoke(
        ToolInvocation(token=write_token, effectId="write-ok", input=write_input)
    )
    assert written["content"]["created"] is True
    digest = written["content"]["sha256"]

    read_input = {"mount": "workspace", "path": "notes/hello.txt", "expectedSha256": digest}
    read_token = _token(
        issuer,
        tool_ref="tool://filesystem/read-text@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="read-ok",
        approved=False,
        input_value=read_input,
    )
    read = await gateway.invoke(
        ToolInvocation(token=read_token, effectId="read-ok", input=read_input)
    )
    assert read["content"]["content"] == "hello"
    assert read["content"]["sha256"] == digest

    bad_hash = {
        "mount": "workspace",
        "path": "notes/hello.txt",
        "expectedSha256": "0" * 64,
    }
    bad_token = _token(
        issuer,
        tool_ref="tool://filesystem/read-text@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="read-bad-hash",
        approved=False,
        input_value=bad_hash,
    )
    with pytest.raises(FilesystemToolError, match="FILESYSTEM_HASH_CONFLICT"):
        await gateway.invoke(
            ToolInvocation(token=bad_token, effectId="read-bad-hash", input=bad_hash)
        )

    for event in audit.events:
        assert "content" not in event.data
        serialized = json.dumps({"data": event.data, "tool": event.tool_ref})
        assert str(tmp_path.resolve()) not in serialized


@pytest.mark.asyncio
async def test_write_create_replace_conflict_and_atomic_failure(tmp_path: Path) -> None:
    gateway, issuer, _ = _gateway(tmp_path)
    tenant = str(uuid4())
    project = str(uuid4())
    create_input = {
        "mount": "workspace",
        "path": "doc.txt",
        "content": "v1",
        "mode": "create",
    }
    create_token = _token(
        issuer,
        tool_ref="tool://filesystem/write-text@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="create-1",
        approved=True,
        input_value=create_input,
    )
    created = await gateway.invoke(
        ToolInvocation(token=create_token, effectId="create-1", input=create_input)
    )
    digest = created["content"]["sha256"]

    conflict = dict(create_input)
    conflict_token = _token(
        issuer,
        tool_ref="tool://filesystem/write-text@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="create-2",
        approved=True,
        input_value=conflict,
    )
    with pytest.raises(FilesystemToolError, match="FILESYSTEM_ALREADY_EXISTS"):
        await gateway.invoke(
            ToolInvocation(token=conflict_token, effectId="create-2", input=conflict)
        )

    replace_bad = {
        "mount": "workspace",
        "path": "doc.txt",
        "content": "v2",
        "mode": "replace",
        "expectedSha256": "0" * 64,
    }
    replace_bad_token = _token(
        issuer,
        tool_ref="tool://filesystem/write-text@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="replace-bad",
        approved=True,
        input_value=replace_bad,
    )
    with pytest.raises(FilesystemToolError, match="FILESYSTEM_HASH_CONFLICT"):
        await gateway.invoke(
            ToolInvocation(token=replace_bad_token, effectId="replace-bad", input=replace_bad)
        )

    replace_ok = {
        "mount": "workspace",
        "path": "doc.txt",
        "content": "v2",
        "mode": "replace",
        "expectedSha256": digest,
    }
    replace_token = _token(
        issuer,
        tool_ref="tool://filesystem/write-text@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="replace-ok",
        approved=True,
        input_value=replace_ok,
    )
    replaced = await gateway.invoke(
        ToolInvocation(token=replace_token, effectId="replace-ok", input=replace_ok)
    )
    assert replaced["content"]["created"] is False
    assert replaced["content"]["sha256"] == hashlib.sha256(b"v2").hexdigest()

    resolver = SafePathResolver(
        root=tmp_path,
        allowed_mounts=frozenset({"workspace"}),
        deny_names=frozenset(),
    )
    path = resolver.resolve(
        tenant_id=tenant,
        project_id=project,
        mount="workspace",
        relative_path="doc.txt",
    ).absolute_path
    assert path.read_text(encoding="utf-8") == "v2"
    assert list(path.parent.glob(".swarmcore-write-*.tmp")) == []


@pytest.mark.asyncio
async def test_effect_journal_replay_and_conflict(tmp_path: Path) -> None:
    gateway, issuer, _ = _gateway(tmp_path)
    tenant = str(uuid4())
    project = str(uuid4())
    write_input = {
        "mount": "workspace",
        "path": "idempotent.txt",
        "content": "once",
        "mode": "create",
    }
    token = _token(
        issuer,
        tool_ref="tool://filesystem/write-text@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="effect-same",
        approved=True,
        input_value=write_input,
    )
    first = await gateway.invoke(
        ToolInvocation(token=token, effectId="effect-same", input=write_input)
    )
    replay = await gateway.invoke(
        ToolInvocation(token=token, effectId="effect-same", input=write_input)
    )
    assert replay == first

    other_input = dict(write_input)
    other_input["content"] = "different"
    other_token = _token(
        issuer,
        tool_ref="tool://filesystem/write-text@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="effect-same",
        approved=True,
        input_value=other_input,
    )
    with pytest.raises(GatewayError, match="effect id was reused"):
        await gateway.invoke(
            ToolInvocation(token=other_token, effectId="effect-same", input=other_input)
        )


@pytest.mark.asyncio
async def test_high_risk_write_requires_approval(tmp_path: Path) -> None:
    gateway, issuer, _ = _gateway(tmp_path)
    write_input = {
        "mount": "workspace",
        "path": "needs-approval.txt",
        "content": "nope",
        "mode": "create",
    }
    token = _token(
        issuer,
        tool_ref="tool://filesystem/write-text@1",
        tenant_id=str(uuid4()),
        project_id=str(uuid4()),
        effect_id="unapproved",
        approved=False,
        input_value=write_input,
    )
    with pytest.raises(GatewayError, match="approved capability"):
        await gateway.invoke(
            ToolInvocation(token=token, effectId="unapproved", input=write_input)
        )


@pytest.mark.asyncio
async def test_unauthorized_mount_and_disabled_fail_closed(tmp_path: Path) -> None:
    gateway, issuer, _ = _gateway(tmp_path)
    bad_mount = {"mount": "secrets", "path": "a.txt"}
    token = _token(
        issuer,
        tool_ref="tool://filesystem/stat@1",
        tenant_id=str(uuid4()),
        project_id=str(uuid4()),
        effect_id="bad-mount",
        approved=False,
        input_value=bad_mount,
    )
    with pytest.raises(FilesystemToolError, match="FILESYSTEM_MOUNT_UNAUTHORIZED"):
        await gateway.invoke(ToolInvocation(token=token, effectId="bad-mount", input=bad_mount))

    disabled = ToolGateway(
        builtin_registry(),
        issuer,
        InMemoryEffectJournal(),
        assemble_tool_executors(
            filesystem=_config(tmp_path, enabled=False, mode=FilesystemExecutorMode.DISABLED)
        ),
    )
    ok_input = {"mount": "workspace", "path": "."}
    disabled_token = _token(
        issuer,
        tool_ref="tool://filesystem/list@1",
        tenant_id=str(uuid4()),
        project_id=str(uuid4()),
        effect_id="disabled",
        approved=False,
        input_value=ok_input,
    )
    with pytest.raises(FilesystemToolError, match="FILESYSTEM_TOOL_DISABLED"):
        await disabled.invoke(
            ToolInvocation(token=disabled_token, effectId="disabled", input=ok_input)
        )


def test_production_forbids_local_mode(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="forbid local"):
        _config(tmp_path, deployment_mode="production", mode=FilesystemExecutorMode.LOCAL)


@pytest.mark.asyncio
async def test_sandbox_unavailable_fail_closed(tmp_path: Path) -> None:
    config = _config(
        tmp_path,
        mode=FilesystemExecutorMode.SANDBOX,
        sandbox_base_url="http://127.0.0.1:9",
        sandbox_image="ghcr.io/swarmcore/filesystem-helper@sha256:" + ("a" * 64),
        sandbox_capability_secret="development-only-capability-secret-32-bytes!!",
    )
    gateway = ToolGateway(
        builtin_registry(),
        CapabilityTokenIssuer("development-only-capability-secret-32-bytes!!"),
        InMemoryEffectJournal(),
        assemble_tool_executors(filesystem=config, sandbox_transport=FailingSandboxTransport()),
    )
    rows = {row["ref"]: row for row in await gateway.readiness()}
    assert rows["tool://filesystem/read-text@1"]["healthy"] is False
    issuer = CapabilityTokenIssuer("development-only-capability-secret-32-bytes!!")
    read_input = {"mount": "workspace", "path": "a.txt"}
    token = _token(
        issuer,
        tool_ref="tool://filesystem/read-text@1",
        tenant_id=str(uuid4()),
        project_id=str(uuid4()),
        effect_id="sandbox-down",
        approved=False,
        input_value=read_input,
    )
    with pytest.raises(FilesystemToolError, match="FILESYSTEM_SANDBOX_UNAVAILABLE"):
        await gateway.invoke(
            ToolInvocation(token=token, effectId="sandbox-down", input=read_input)
        )


@pytest.mark.asyncio
async def test_list_and_stat_do_not_create_directories(tmp_path: Path) -> None:
    gateway, issuer, _ = _gateway(tmp_path)
    tenant = str(uuid4())
    project = str(uuid4())
    list_input = {"mount": "workspace", "path": "."}
    token = _token(
        issuer,
        tool_ref="tool://filesystem/list@1",
        tenant_id=tenant,
        project_id=project,
        effect_id="list-missing",
        approved=False,
        input_value=list_input,
    )
    with pytest.raises(FilesystemToolError, match="FILESYSTEM_NOT_FOUND"):
        await gateway.invoke(ToolInvocation(token=token, effectId="list-missing", input=list_input))
    resolver = SafePathResolver(
        root=tmp_path,
        allowed_mounts=frozenset({"workspace"}),
        deny_names=frozenset(),
    )
    assert not resolver.project_root(tenant_id=tenant, project_id=project).exists()


def test_tool_gateway_and_worker_share_factory(tmp_path: Path) -> None:
    config = _config(tmp_path)
    api_executors = assemble_tool_executors(filesystem=config)
    worker_executors = assemble_tool_executors(filesystem=config)
    assert set(api_executors) == set(worker_executors)
    assert FILESYSTEM_OPERATIONS.issubset(api_executors)
