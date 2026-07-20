from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from swarmcore_registry import builtin_registry
from swarmcore_tool_gateway import (
    AuditEvent,
    CapabilityTokenIssuer,
    EffectConflict,
    GatewayError,
    InMemoryEffectJournal,
    ToolExecutionContext,
    ToolGateway,
    ToolInvocation,
)

SECRET = "unit-test-capability-secret-at-least-32-bytes"


class Audit:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def record(self, event: AuditEvent) -> None:
        self.events.append(event)


def token(
    issuer: CapabilityTokenIssuer,
    *,
    tool_ref: str = "tool://search@1",
    effect_id: str | None = "effect-1",
    approved: bool = False,
) -> str:
    return issuer.issue(
        tenant_id="00000000-0000-0000-0000-000000000001",
        project_id="00000000-0000-0000-0000-000000000002",
        run_id="00000000-0000-0000-0000-000000000003",
        node_key="tool",
        tool_ref=tool_ref,
        execution_id="execution-1",
        effect_id=effect_id,
        approved=approved,
    )


@pytest.mark.asyncio
async def test_confirmed_effect_is_returned_without_repeating_side_effect() -> None:
    calls: list[str] = []
    audit = Audit()
    issuer = CapabilityTokenIssuer(SECRET, clock=lambda: datetime(2026, 7, 16, tzinfo=UTC))

    async def executor(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
        calls.append(effect_id)
        return {"items": [input_value["query"]]}

    gateway = ToolGateway(
        builtin_registry(),
        issuer,
        InMemoryEffectJournal(),
        {"builtin.search": executor},
        audit,
    )
    invocation = ToolInvocation(token=token(issuer), effectId="effect-1", input={"query": "swarm"})

    first = await gateway.invoke(invocation)
    second = await gateway.invoke(invocation)

    assert first == second
    assert calls == ["effect-1"]
    assert [event.type for event in audit.events] == [
        "tool.started",
        "tool.completed",
    ]


@pytest.mark.asyncio
async def test_effect_id_cannot_be_reused_with_different_input() -> None:
    issuer = CapabilityTokenIssuer(SECRET)

    async def executor(input_value: dict[str, Any], effect_id: str) -> dict[str, Any]:
        return {"items": [input_value, effect_id]}

    gateway = ToolGateway(
        builtin_registry(),
        issuer,
        InMemoryEffectJournal(),
        {"builtin.search": executor},
    )
    capability = token(issuer)
    await gateway.invoke(
        ToolInvocation(token=capability, effectId="effect-1", input={"query": "one"})
    )
    with pytest.raises(EffectConflict):
        await gateway.invoke(
            ToolInvocation(token=capability, effectId="effect-1", input={"query": "two"})
        )


@pytest.mark.asyncio
async def test_high_risk_tool_requires_approved_capability() -> None:
    issuer = CapabilityTokenIssuer(SECRET)
    gateway = ToolGateway(builtin_registry(), issuer, InMemoryEffectJournal(), executors={})
    invocation = ToolInvocation(
        token=token(issuer, tool_ref="tool://publish-report@1"),
        effectId="effect-1",
        input={"reports": {}},
    )

    with pytest.raises(GatewayError, match="requires an approved capability"):
        await gateway.invoke(invocation)


@pytest.mark.asyncio
async def test_token_scope_and_input_schema_are_enforced() -> None:
    issuer = CapabilityTokenIssuer(SECRET)
    gateway = ToolGateway(builtin_registry(), issuer, InMemoryEffectJournal(), executors={})
    with pytest.raises(GatewayError, match="effect id"):
        await gateway.invoke(
            ToolInvocation(token=token(issuer), effectId="other", input={"query": "ok"})
        )
    with pytest.raises(GatewayError, match="input schema"):
        await gateway.invoke(ToolInvocation(token=token(issuer), effectId="effect-1", input={}))


@pytest.mark.asyncio
async def test_contextual_executor_uses_authorized_scope_and_is_idempotent() -> None:
    issuer = CapabilityTokenIssuer(SECRET)
    contexts: list[ToolExecutionContext] = []

    class Recorder:
        async def execute(
            self,
            input_value: dict[str, Any],
            effect_id: str,
            context: ToolExecutionContext,
        ) -> dict[str, Any]:
            contexts.append(context)
            return {
                "evaluationId": input_value["evaluationId"],
                "recorded": True,
                "effectId": effect_id,
                "resultHash": "0" * 64,
            }

    gateway = ToolGateway(
        builtin_registry(),
        issuer,
        InMemoryEffectJournal(),
        {"workbench.record_evaluation": Recorder()},
    )
    input_value = {
        "evaluationId": "00000000-0000-0000-0000-000000000004",
        "result": {
            "passed": True,
            "ruleSetVersionId": "rules-1",
            "attachmentManifestHash": "manifest",
            "checks": {"requirements": 0, "attachments": 0},
            "findings": [],
        },
    }
    unauthorized = issuer.issue(
        tenant_id="00000000-0000-0000-0000-000000000001",
        project_id="00000000-0000-0000-0000-000000000002",
        run_id="00000000-0000-0000-0000-000000000003",
        node_key="tool",
        tool_ref="tool://workbench/record-evaluation@1",
        execution_id="execution-1",
        effect_id="effect-1",
        approved=False,
        action="tool.compensate",
    )
    with pytest.raises(GatewayError, match="does not allow"):
        await gateway.invoke(
            ToolInvocation(token=unauthorized, effectId="effect-1", input=input_value)
        )

    authorized = token(issuer, tool_ref="tool://workbench/record-evaluation@1")
    invocation = ToolInvocation(token=authorized, effectId="effect-1", input=input_value)
    assert await gateway.invoke(invocation) == await gateway.invoke(invocation)
    assert contexts == [
        ToolExecutionContext(
            tenant_id="00000000-0000-0000-0000-000000000001",
            project_id="00000000-0000-0000-0000-000000000002",
            run_id="00000000-0000-0000-0000-000000000003",
            node_key="tool",
            tool_ref="tool://workbench/record-evaluation@1",
            execution_id="execution-1",
        )
    ]
