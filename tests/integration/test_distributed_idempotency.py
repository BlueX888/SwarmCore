from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import create_async_engine
from swarmcore_application import RunService
from swarmcore_compiler import Compiler, sequential
from swarmcore_persistence import Database, RunCommandRepository, tenant_transaction
from swarmcore_persistence.models import Run, RunCommand, Strategy, StrategyVersion
from swarmcore_registry import builtin_registry


@pytest.mark.asyncio
async def test_run_and_command_idempotency_are_safe_across_sessions() -> None:
    database_url = os.getenv("SWARMCORE_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("SWARMCORE_TEST_DATABASE_URL is not configured")

    tenant_id, project_id = uuid4(), uuid4()
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO tenants (id, name, status, created_at, updated_at) "
                "VALUES (:tenant, :name, 'ACTIVE', now(), now())"
            ),
            {"tenant": tenant_id, "name": f"idempotency-{tenant_id}"},
        )
        await connection.execute(
            text("SELECT set_config('app.tenant_id', :tenant, true)"),
            {"tenant": str(tenant_id)},
        )
        await connection.execute(
            text(
                "INSERT INTO projects "
                "(id, tenant_id, name, settings, created_at, updated_at) "
                "VALUES (:project, :tenant, 'idempotency', '{}', now(), now())"
            ),
            {"project": project_id, "tenant": tenant_id},
        )
    await engine.dispose()

    raw_spec = sequential(
        "idempotency", {"worker": {"role": "worker", "instructions": "work"}}
    )
    plan = Compiler().compile(
        raw_spec,
        registry_snapshot=builtin_registry().snapshot_id,
        policy_revision="test",
    )
    database = Database(database_url)
    try:
        async with tenant_transaction(
            database.sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            strategy = Strategy(
                tenant_id=tenant_id,
                project_id=project_id,
                name="idempotency",
            )
            session.add(strategy)
            await session.flush()
            version = StrategyVersion(
                tenant_id=tenant_id,
                strategy_id=strategy.id,
                version=1,
                raw_spec=raw_spec.model_dump(mode="json", by_alias=True),
                normalized_spec=raw_spec.model_dump(mode="json", by_alias=True),
                plan=plan.model_dump(mode="json", by_alias=True),
                plan_hash=plan.plan_hash,
                schema_version=raw_spec.api_version,
                runtime_version=plan.runtime_version,
            )
            session.add(version)
            await session.flush()
            version_id = version.id

        async def create_run() -> tuple[Run, object]:
            async with tenant_transaction(
                database.sessions, tenant_id=tenant_id, project_id=project_id
            ) as session:
                return await RunService().create(
                    session,
                    tenant_id=tenant_id,
                    project_id=project_id,
                    strategy_version_id=version_id,
                    input_data={},
                    idempotency_key="same-run",
                )

        first, second = await asyncio.gather(create_run(), create_run())
        assert first[0].id == second[0].id
        run_id = first[0].id

        request_id = uuid4()

        async def append_command() -> RunCommand:
            async with tenant_transaction(
                database.sessions, tenant_id=tenant_id, project_id=project_id
            ) as session:
                return await RunCommandRepository().append(
                    session,
                    tenant_id=tenant_id,
                    run_id=run_id,
                    command_type="cancel",
                    request_id=request_id,
                    payload={},
                )

        command_a, command_b = await asyncio.gather(
            append_command(), append_command()
        )
        assert command_a.id == command_b.id
        async with tenant_transaction(
            database.sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            assert (
                await session.scalar(
                    select(func.count(Run.id)).where(Run.id == run_id)
                )
                == 1
            )
            assert (
                await session.scalar(
                    select(func.count(RunCommand.id)).where(
                        RunCommand.run_id == run_id,
                        RunCommand.request_id == request_id,
                    )
                )
                == 1
            )
    finally:
        await database.dispose()
