from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.asyncio
async def test_migrated_postgres_enforces_tenant_rls() -> None:
    database_url = os.getenv("SWARMCORE_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("SWARMCORE_TEST_DATABASE_URL is not configured")

    engine = create_async_engine(database_url)
    tenant_a, tenant_b = uuid4(), uuid4()
    project_a, project_b = uuid4(), uuid4()
    role = f"swarmcore_rls_probe_{uuid4().hex}"
    async with engine.connect() as connection:
        transaction = await connection.begin()
        try:
            await connection.execute(text(f'CREATE ROLE "{role}" NOLOGIN'))
            await connection.execute(
                text(
                    "INSERT INTO tenants (id, name, status, created_at, updated_at) "
                    "VALUES (:a, :an, 'ACTIVE', now(), now()), "
                    "(:b, :bn, 'ACTIVE', now(), now())"
                ),
                {
                    "a": tenant_a,
                    "an": f"tenant-{tenant_a}",
                    "b": tenant_b,
                    "bn": f"tenant-{tenant_b}",
                },
            )
            await connection.execute(
                text(
                    "INSERT INTO projects "
                    "(id, tenant_id, name, settings, created_at, updated_at) "
                    "VALUES (:pa, :a, 'a', '{}', now(), now()), "
                    "(:pb, :b, 'b', '{}', now(), now())"
                ),
                {"pa": project_a, "a": tenant_a, "pb": project_b, "b": tenant_b},
            )
            await connection.execute(text(f'GRANT SELECT ON projects TO "{role}"'))
            await connection.execute(text(f'SET LOCAL ROLE "{role}"'))
            await connection.execute(
                text("SELECT set_config('app.tenant_id', :tenant, true)"),
                {"tenant": str(tenant_a)},
            )
            own_count = await connection.scalar(text("SELECT count(*) FROM projects"))
            leaked_count = await connection.scalar(
                text("SELECT count(*) FROM projects WHERE id = :project"),
                {"project": project_b},
            )
            assert own_count == 1
            assert leaked_count == 0
        finally:
            await transaction.rollback()
            await engine.dispose()
