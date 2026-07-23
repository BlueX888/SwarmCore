from __future__ import annotations

from copy import deepcopy
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from swarmcore_application import StrategyService
from swarmcore_capability_contract_post_evaluation import STRATEGIES
from swarmcore_persistence.errors import PersistenceConflictError
from swarmcore_persistence.models import Strategy, StrategyVersion
from swarmcore_registry import builtin_registry


@pytest.mark.asyncio
async def test_trusted_strategy_reuses_same_spec_when_registry_snapshot_expands() -> None:
    raw_spec = next(iter(STRATEGIES.values()))
    strategy = MagicMock(spec=Strategy)
    strategy.id = uuid4()
    existing = MagicMock(spec=StrategyVersion)
    existing.raw_spec = deepcopy(raw_spec)
    existing.plan_hash = "historical-registry-plan-hash"
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[strategy, existing])

    value = await StrategyService().ensure_trusted_version(
        session,
        tenant_id=uuid4(),
        project_id=uuid4(),
        reference="strategy://contract-post-evaluation/generate@6",
        raw_spec=raw_spec,
        registry_snapshot=builtin_registry().snapshot_id,
        policy_revision="test",
        actor="test",
    )

    assert value is existing
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_trusted_strategy_rejects_changed_spec_at_same_version() -> None:
    raw_spec = next(iter(STRATEGIES.values()))
    changed = deepcopy(raw_spec)
    changed["metadata"]["name"] = "changed"
    strategy = MagicMock(spec=Strategy)
    strategy.id = uuid4()
    existing = MagicMock(spec=StrategyVersion)
    existing.raw_spec = raw_spec
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[strategy, existing])

    with pytest.raises(PersistenceConflictError, match="immutable"):
        await StrategyService().ensure_trusted_version(
            session,
            tenant_id=uuid4(),
            project_id=uuid4(),
            reference="strategy://contract-post-evaluation/generate@6",
            raw_spec=changed,
            registry_snapshot=builtin_registry().snapshot_id,
            policy_revision="test",
            actor="test",
        )
