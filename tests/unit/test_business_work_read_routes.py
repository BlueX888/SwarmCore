from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from swarmcore_api import create_app
from swarmcore_api.dependencies import RequestScope
from swarmcore_api.routes import list_run_summaries
from swarmcore_api.settings import Settings


def test_business_work_read_routes_precede_dynamic_strategy_route() -> None:
    app = create_app(Settings(telemetry_enabled=False))
    routes = [
        (frozenset(route.methods or ()), route.path)
        for route in app.routes
        if hasattr(route, "path") and hasattr(route, "methods")
    ]

    strategy_versions = (frozenset({"GET"}), "/v1/projects/{project_id}/strategies/versions")
    run_summaries = (frozenset({"GET"}), "/v1/projects/{project_id}/run-summaries")
    dynamic_strategy = (frozenset({"GET"}), "/v1/projects/{project_id}/strategies/{strategy_id}")
    assert strategy_versions in routes
    assert run_summaries in routes
    assert routes.index(strategy_versions) < routes.index(dynamic_strategy)


@pytest.mark.asyncio
async def test_run_summaries_merge_recent_and_active_runs_with_bulk_task_counts() -> None:
    tenant_id = uuid4()
    project_id = uuid4()
    strategy_version_id = uuid4()
    now = datetime.now(UTC)
    completed = SimpleNamespace(
        id=uuid4(),
        status="FAILED",
        strategy_version_id=strategy_version_id,
        next_event_seq=4,
        created_at=now,
        started_at=now,
        completed_at=now + timedelta(seconds=2),
        input={},
        output={},
        initiated_by="system",
    )
    active = SimpleNamespace(
        id=uuid4(),
        status="ACCEPTED",
        strategy_version_id=strategy_version_id,
        next_event_seq=2,
        created_at=now - timedelta(seconds=1),
        started_at=None,
        completed_at=None,
        input={"provenance": {"operatorName": "李雷"}},
        output=None,
        initiated_by="system",
    )
    session = MagicMock()
    session.scalars = AsyncMock(side_effect=[[completed], [active]])
    task_rows = [(completed.id, 2), (active.id, 1)]
    session.execute = AsyncMock(
        side_effect=[task_rows, [(completed.id, "run.failed", {"message": "网络异常"})]]
    )
    session.scalar = AsyncMock(return_value=2)

    response = await list_run_summaries(
        RequestScope(
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id="tester",
            roles=(),
            scopes=(),
            auth_context_hash="test",
        ),
        session,
        strategy_version_id=strategy_version_id,
        limit=1,
        include_active=True,
    )

    assert [item.run_id for item in response.items] == [completed.id, active.id]
    assert response.items[0].task_count == 2
    assert response.items[1].operator_name == "李雷"
    assert response.items[0].event_count == 3
    assert response.items[0].failure_reason == "网络异常"
    assert response.total == 2
