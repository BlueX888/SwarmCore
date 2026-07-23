from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine
from swarmcore_application import BusinessObjectService, ConnectionService, ResourceCatalogService
from swarmcore_persistence import Database, tenant_transaction
from swarmcore_persistence.models import BusinessObjectVersion


@pytest.mark.asyncio
async def test_business_context_resource_plane_rls_immutability_and_secret_boundary() -> None:
    database_url = os.getenv("SWARMCORE_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("SWARMCORE_TEST_DATABASE_URL is not configured")
    tenant_id, other_tenant_id, project_id, other_project_id = (
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
    )
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "INSERT INTO tenants (id, name, status, created_at, updated_at) "
                "VALUES (:tenant, :name, 'ACTIVE', now(), now()), "
                "(:other, :other_name, 'ACTIVE', now(), now())"
            ),
            {
                "tenant": tenant_id,
                "name": f"context-{tenant_id}",
                "other": other_tenant_id,
                "other_name": f"context-{other_tenant_id}",
            },
        )
        for tenant, project, name in (
            (tenant_id, project_id, "context-project"),
            (other_tenant_id, other_project_id, "other-project"),
        ):
            await connection.execute(
                text("SELECT set_config('app.tenant_id', :tenant, true)"),
                {"tenant": str(tenant)},
            )
            await connection.execute(
                text(
                    "INSERT INTO projects "
                    "(id, tenant_id, name, settings, created_at, updated_at) "
                    "VALUES (:project, :tenant, :name, '{}', now(), now())"
                ),
                {"project": project, "tenant": tenant, "name": name},
            )
    await engine.dispose()

    database = Database(database_url)
    objects = BusinessObjectService()
    connections = ConnectionService()
    resources = ResourceCatalogService()
    async with tenant_transaction(
        database.sessions, tenant_id=tenant_id, project_id=project_id
    ) as session:
        business_object, first, created = await objects.upsert(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            object_type="contract",
            canonical_key="PO-100",
            schema_ref="schema://contract/facts@1",
            data={"amount": 100},
            provenance={"source": "integration"},
            actor="integration",
        )
        _, same, duplicate_created = await objects.upsert(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            object_type="contract",
            canonical_key="PO-100",
            schema_ref="schema://contract/facts@1",
            data={"amount": 100},
            provenance={"source": "retry"},
            actor="integration",
        )
        assert created and not duplicate_created and same.id == first.id
        connection, version = await connections.create(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            name="fake-files",
            connector_ref="connector://fake/files@1",
            configuration={"endpoint": "memory://contracts"},
            credential_ref="vault://integration/fake-files",
            policy_ref=None,
            actor="integration",
        )
        resource = await resources.create(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            connection_id=connection.id,
            resource_kind="DOCUMENT_COLLECTION",
            name="contracts",
            locator={"path": "contracts"},
            schema_ref=None,
            media_type="application/pdf",
            sensitivity="CONFIDENTIAL",
            actor="integration",
        )
        assert version.credential_ref.startswith("vault://")
        assert resource.connection_id == connection.id

    role = f"swarmcore_context_probe_{uuid4().hex}"
    probe = create_async_engine(database_url)
    async with probe.connect() as connection:
        transaction = await connection.begin()
        try:
            await connection.execute(text(f'CREATE ROLE "{role}" NOLOGIN'))
            await connection.execute(text(f'GRANT SELECT ON business_objects TO "{role}"'))
            await connection.execute(text(f'SET LOCAL ROLE "{role}"'))
            await connection.execute(
                text("SELECT set_config('app.tenant_id', :tenant, true)"),
                {"tenant": str(other_tenant_id)},
            )
            await connection.execute(
                text("SELECT set_config('app.project_id', :project, true)"),
                {"project": str(other_project_id)},
            )
            assert (
                await connection.scalar(
                    text("SELECT count(*) FROM business_objects WHERE id = :id"),
                    {"id": business_object.id},
                )
                == 0
            )
        finally:
            await transaction.rollback()
    await probe.dispose()

    with pytest.raises(DBAPIError):
        async with tenant_transaction(
            database.sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            await session.execute(
                update(BusinessObjectVersion)
                .where(BusinessObjectVersion.id == first.id)
                .values(data={"amount": 999})
            )
    await database.dispose()
