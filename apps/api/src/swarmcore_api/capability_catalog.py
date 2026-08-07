from __future__ import annotations

from uuid import UUID

from swarmcore_application import CapabilityCatalog, ConfigurationKind, ProjectConfigurationService
from swarmcore_application.capabilities import ModelCapability
from swarmcore_application.project_models import (
    is_runtime_provider_name,
    project_model_logical_id,
)
from swarmcore_persistence import Database, tenant_transaction


async def project_capability_catalog(
    database: Database,
    *,
    base_catalog: CapabilityCatalog,
    tenant_id: UUID,
    project_id: UUID,
) -> CapabilityCatalog:
    """Return the same project-aware catalog to every transport."""
    try:
        async with tenant_transaction(
            database.sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            rows, _ = await ProjectConfigurationService().list(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                kind=ConfigurationKind.MODEL,
                limit=1000,
            )
    except Exception:
        return base_catalog
    project_models = [
        ModelCapability(
            ref=f"{project_model_logical_id(str(row.source_ref))}@{row.revision}",
            runtime="agno",
            environments=["development", "production"],
        )
        for row in rows
        if is_runtime_provider_name(row.name) and str(row.source_ref).startswith("model://project/")
    ]
    if not project_models:
        return base_catalog
    return base_catalog.model_copy(update={"models": [*project_models, *base_catalog.models]})
