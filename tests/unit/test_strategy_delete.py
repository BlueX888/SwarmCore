from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from swarmcore_application import StrategyDeleteError, StrategyService
from swarmcore_persistence.models import Strategy, StrategyDraft


def test_build_delete_blockers_allows_active_draft_only_strategy() -> None:
    blockers = StrategyService.build_delete_blockers(
        lifecycle="ACTIVE",
        version_count=0,
        run_count=0,
        assessment_count=0,
        business_work_count=0,
    )
    assert blockers == ()


@pytest.mark.parametrize(
    ("lifecycle", "code"),
    [
        ("TRUSTED", "STRATEGY_DELETE_NOT_ALLOWED"),
        ("EPHEMERAL", "STRATEGY_DELETE_NOT_ALLOWED"),
        ("ARCHIVED", "STRATEGY_DELETE_NOT_ALLOWED"),
    ],
)
def test_build_delete_blockers_rejects_system_managed_lifecycle(
    lifecycle: str, code: str
) -> None:
    blockers = StrategyService.build_delete_blockers(
        lifecycle=lifecycle,
        version_count=0,
        run_count=0,
        assessment_count=0,
        business_work_count=0,
    )
    assert any(item.code == code for item in blockers)


def test_build_delete_blockers_collects_all_reference_codes() -> None:
    blockers = StrategyService.build_delete_blockers(
        lifecycle="ACTIVE",
        version_count=2,
        run_count=5,
        assessment_count=3,
        business_work_count=1,
    )
    assert [item.code for item in blockers] == [
        "STRATEGY_HAS_PUBLISHED_VERSIONS",
        "STRATEGY_IN_USE_BY_RUN",
        "STRATEGY_IN_USE_BY_ASSESSMENT",
        "STRATEGY_IN_USE_BY_BUSINESS_WORK",
    ]
    assert [item.count for item in blockers] == [2, 5, 3, 1]


@pytest.mark.asyncio
async def test_delete_removes_draft_only_strategy_and_writes_audit() -> None:
    strategy = MagicMock(spec=Strategy)
    strategy.id = uuid4()
    strategy.name = "draft-only"
    strategy.lifecycle = "ACTIVE"
    strategy.project_id = uuid4()
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[strategy, 0, 1])
    session.scalars = AsyncMock(return_value=[])
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    service = StrategyService()
    service._audit = MagicMock()
    service._audit.append = AsyncMock()

    await service.delete(
        session,
        tenant_id=uuid4(),
        project_id=strategy.project_id,
        strategy_id=strategy.id,
        actor="author@example.com",
    )

    service._audit.append.assert_awaited_once()
    audit_kwargs = service._audit.append.await_args.kwargs
    assert audit_kwargs["action"] == "strategy.delete"
    assert audit_kwargs["resource_id"] == str(strategy.id)
    assert audit_kwargs["metadata"] == {
        "name": "draft-only",
        "lifecycle": "ACTIVE",
        "draftCount": 1,
    }
    session.delete.assert_awaited_once_with(strategy)
    session.flush.assert_awaited()


@pytest.mark.asyncio
async def test_delete_rejects_when_published_versions_exist() -> None:
    strategy = MagicMock(spec=Strategy)
    strategy.id = uuid4()
    strategy.name = "published"
    strategy.lifecycle = "ACTIVE"
    strategy.project_id = uuid4()
    version_id = uuid4()
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[strategy, 1, 0, 0, 0])
    session.scalars = AsyncMock(return_value=[version_id])
    service = StrategyService()

    with pytest.raises(StrategyDeleteError) as captured:
        await service.delete(
            session,
            tenant_id=uuid4(),
            project_id=strategy.project_id,
            strategy_id=strategy.id,
            actor="author@example.com",
        )

    assert captured.value.code == "STRATEGY_DELETE_BLOCKED"
    assert any(
        item.code == "STRATEGY_HAS_PUBLISHED_VERSIONS" for item in captured.value.blockers
    )
    session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_get_delete_impact_matches_delete_rules() -> None:
    strategy = MagicMock(spec=Strategy)
    strategy.id = uuid4()
    strategy.name = "trusted-pack"
    strategy.lifecycle = "TRUSTED"
    strategy.project_id = uuid4()
    session = MagicMock()
    session.scalar = AsyncMock(side_effect=[strategy, 0])
    session.scalars = AsyncMock(return_value=[])
    service = StrategyService()

    impact = await service.get_delete_impact(
        session,
        tenant_id=uuid4(),
        project_id=strategy.project_id,
        strategy_id=strategy.id,
    )

    assert impact.deletable is False
    assert impact.blockers[0].code == "STRATEGY_DELETE_NOT_ALLOWED"

    session.scalar = AsyncMock(side_effect=[strategy, 0])
    session.scalars = AsyncMock(return_value=[])
    with pytest.raises(StrategyDeleteError) as captured:
        await service.delete(
            session,
            tenant_id=uuid4(),
            project_id=strategy.project_id,
            strategy_id=strategy.id,
            actor="author@example.com",
        )
    assert captured.value.blockers == impact.blockers


@pytest.mark.asyncio
async def test_delete_requires_project_scope() -> None:
    session = MagicMock()
    session.scalar = AsyncMock(return_value=None)
    service = StrategyService()

    with pytest.raises(LookupError, match="strategy not found"):
        await service.delete(
            session,
            tenant_id=uuid4(),
            project_id=uuid4(),
            strategy_id=uuid4(),
            actor="author@example.com",
        )


@pytest.mark.asyncio
async def test_delete_blocks_run_and_assessment_and_business_work_refs() -> None:
    strategy = MagicMock(spec=Strategy)
    strategy.id = uuid4()
    strategy.name = "in-use"
    strategy.lifecycle = "ACTIVE"
    strategy.project_id = uuid4()
    version_id = uuid4()
    session = MagicMock()
    # lock strategy, version_count, run_count, assessment_count, business_work_count
    session.scalar = AsyncMock(side_effect=[strategy, 1, 4, 2, 1])
    session.scalars = AsyncMock(return_value=[version_id])
    service = StrategyService()

    with pytest.raises(StrategyDeleteError) as captured:
        await service.delete(
            session,
            tenant_id=uuid4(),
            project_id=strategy.project_id,
            strategy_id=strategy.id,
            actor="author@example.com",
        )

    codes = {item.code for item in captured.value.blockers}
    assert codes == {
        "STRATEGY_HAS_PUBLISHED_VERSIONS",
        "STRATEGY_IN_USE_BY_RUN",
        "STRATEGY_IN_USE_BY_ASSESSMENT",
        "STRATEGY_IN_USE_BY_BUSINESS_WORK",
    }


@pytest.mark.asyncio
async def test_get_delete_impact_missing_strategy() -> None:
    session = MagicMock()
    session.scalar = AsyncMock(return_value=None)
    with pytest.raises(LookupError, match="strategy not found"):
        await StrategyService().get_delete_impact(
            session,
            tenant_id=uuid4(),
            project_id=uuid4(),
            strategy_id=uuid4(),
        )


def test_draft_model_cascades_with_strategy() -> None:
    assert StrategyDraft.__table__.foreign_key_constraints
    cascade = next(
        constraint
        for constraint in StrategyDraft.__table__.foreign_key_constraints
        if "strategy_id" in constraint.column_keys
    )
    assert cascade.ondelete == "CASCADE"
