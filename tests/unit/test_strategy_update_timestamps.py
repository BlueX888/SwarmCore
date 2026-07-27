from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from swarmcore_application import StrategyService
from swarmcore_persistence.models import Strategy, StrategyDraft


def _valid_raw_spec(name: str = "draft-strategy") -> dict:
    return {
        "apiVersion": "swarmcore.io/v1",
        "kind": "SwarmStrategy",
        "metadata": {"name": name},
        "spec": {
            "inputSchema": {"type": "object"},
            "outputSchema": {"type": "object"},
            "defaults": {"model": "model://fake-deterministic"},
            "agents": {"one": {"role": "worker", "instructions": "work"}},
            "graph": {
                "entrypoint": "one",
                "nodes": {"one": {"type": "agent", "agent": "one"}},
                "output": {},
            },
        },
    }


@pytest.mark.asyncio
async def test_update_draft_bumps_strategy_updated_at() -> None:
    tenant_id = uuid4()
    strategy_id = uuid4()
    draft_id = uuid4()
    project_id = uuid4()
    older = datetime(2026, 7, 1, tzinfo=UTC)

    strategy = MagicMock(spec=Strategy)
    strategy.id = strategy_id
    strategy.project_id = project_id
    strategy.updated_at = older

    draft = MagicMock(spec=StrategyDraft)
    draft.id = draft_id
    draft.strategy_id = strategy_id
    draft.tenant_id = tenant_id
    draft.revision = 1
    draft.updated_at = older
    draft.editor_state = {}
    draft.diagnostics = ["stale"]

    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[draft, strategy])
    session.flush = AsyncMock()

    service = StrategyService()
    service._audit = MagicMock()
    service._audit.append = AsyncMock()

    before = datetime.now(UTC)
    result = await service.update_draft(
        session,
        tenant_id=tenant_id,
        strategy_id=strategy_id,
        draft_id=draft_id,
        expected_revision=1,
        raw_spec=_valid_raw_spec(),
        actor="author@example.com",
    )
    after = datetime.now(UTC)

    assert result is draft
    assert draft.revision == 2
    assert draft.updated_by == "author@example.com"
    assert draft.diagnostics == []
    assert older < draft.updated_at <= after
    assert draft.updated_at >= before - timedelta(seconds=1)
    assert strategy.updated_at == draft.updated_at
    session.flush.assert_awaited()
    service._audit.append.assert_awaited_once()


@pytest.mark.asyncio
async def test_publish_bumps_strategy_updated_at() -> None:
    tenant_id = uuid4()
    strategy_id = uuid4()
    draft_id = uuid4()
    project_id = uuid4()
    older = datetime(2026, 7, 1, tzinfo=UTC)
    raw_spec = _valid_raw_spec()

    strategy = MagicMock(spec=Strategy)
    strategy.id = strategy_id
    strategy.project_id = project_id
    strategy.updated_at = older

    draft = MagicMock(spec=StrategyDraft)
    draft.id = draft_id
    draft.strategy_id = strategy_id
    draft.tenant_id = tenant_id
    draft.raw_spec = raw_spec

    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[strategy, draft, 0])
    session.add = MagicMock()
    session.flush = AsyncMock()

    service = StrategyService()
    service.compile = MagicMock(return_value=(MagicMock(
        api_version="swarmcore.io/v1",
        model_dump=MagicMock(return_value={}),
    ), MagicMock(
        plan_hash="a" * 64,
        runtime_version="1.0.0",
        model_dump=MagicMock(return_value={}),
    )))
    service._audit = MagicMock()
    service._audit.append = AsyncMock()

    before = datetime.now(UTC)
    await service.publish(
        session,
        tenant_id=tenant_id,
        strategy_id=strategy_id,
        draft_id=draft_id,
        registry_snapshot="registry",
        policy_revision="policy",
        actor="author@example.com",
    )
    after = datetime.now(UTC)

    assert before - timedelta(seconds=1) <= strategy.updated_at <= after
    assert strategy.updated_at > older
    session.add.assert_called_once()
    session.flush.assert_awaited()
