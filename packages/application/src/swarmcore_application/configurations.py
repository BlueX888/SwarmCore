from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.errors import PersistenceConflictError
from swarmcore_persistence.models import ProjectConfiguration
from swarmcore_registry import RegistrySnapshot, builtin_registry


class ConfigurationKind(StrEnum):
    AGENT = "agent"
    TOOL = "tool"
    MODEL = "model"


class ProjectConfigurationService:
    def __init__(self, registry: RegistrySnapshot | None = None) -> None:
        self._registry = registry or builtin_registry()
        self._audit = AuditRepository()

    async def create(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        kind: ConfigurationKind,
        name: str,
        source_ref: str,
        configuration: dict[str, Any],
        actor: str,
    ) -> ProjectConfiguration:
        clean_name = name.strip()
        clean_ref = source_ref.strip()
        self.validate(kind=kind, name=clean_name, source_ref=clean_ref, configuration=configuration)
        existing = await session.scalar(
            select(ProjectConfiguration.id).where(
                ProjectConfiguration.tenant_id == tenant_id,
                ProjectConfiguration.project_id == project_id,
                ProjectConfiguration.kind == kind.value,
                ProjectConfiguration.name == clean_name,
            )
        )
        if existing is not None:
            raise PersistenceConflictError("configuration name already exists in this project")
        saved = ProjectConfiguration(
            tenant_id=tenant_id,
            project_id=project_id,
            kind=kind.value,
            name=clean_name,
            source_ref=clean_ref,
            configuration=configuration,
            created_by=actor,
            updated_by=actor,
        )
        session.add(saved)
        await session.flush()
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="configuration.create",
            resource_type=f"{kind.value}_configuration",
            resource_id=str(saved.id),
            metadata={"name": clean_name, "sourceRef": clean_ref},
        )
        return saved

    async def list(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        kind: ConfigurationKind,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ProjectConfiguration], int]:
        scope = (
            ProjectConfiguration.tenant_id == tenant_id,
            ProjectConfiguration.project_id == project_id,
            ProjectConfiguration.kind == kind.value,
        )
        items = list(
            await session.scalars(
                select(ProjectConfiguration)
                .where(*scope)
                .order_by(ProjectConfiguration.updated_at.desc(), ProjectConfiguration.id)
                .offset(offset)
                .limit(limit)
            )
        )
        total = await session.scalar(
            select(func.count()).select_from(ProjectConfiguration).where(*scope)
        )
        return items, total or 0

    async def update(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        kind: ConfigurationKind,
        configuration_id: UUID,
        name: str,
        source_ref: str,
        configuration: dict[str, Any],
        actor: str,
    ) -> ProjectConfiguration:
        clean_name = name.strip()
        clean_ref = source_ref.strip()
        self.validate(kind=kind, name=clean_name, source_ref=clean_ref, configuration=configuration)
        saved = await session.scalar(
            select(ProjectConfiguration).where(
                ProjectConfiguration.id == configuration_id,
                ProjectConfiguration.tenant_id == tenant_id,
                ProjectConfiguration.project_id == project_id,
                ProjectConfiguration.kind == kind.value,
            )
        )
        if saved is None:
            raise LookupError("configuration not found")
        duplicate = await session.scalar(
            select(ProjectConfiguration.id).where(
                ProjectConfiguration.tenant_id == tenant_id,
                ProjectConfiguration.project_id == project_id,
                ProjectConfiguration.kind == kind.value,
                ProjectConfiguration.name == clean_name,
                ProjectConfiguration.id != configuration_id,
            )
        )
        if duplicate is not None:
            raise PersistenceConflictError("configuration name already exists in this project")
        saved.name = clean_name
        saved.source_ref = clean_ref
        saved.configuration = configuration
        saved.revision += 1
        saved.updated_by = actor
        await session.flush()
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="configuration.update",
            resource_type=f"{kind.value}_configuration",
            resource_id=str(saved.id),
            metadata={"name": clean_name, "sourceRef": clean_ref, "revision": saved.revision},
        )
        return saved

    async def delete(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        kind: ConfigurationKind,
        configuration_id: UUID,
        actor: str,
    ) -> None:
        saved = await session.scalar(
            select(ProjectConfiguration).where(
                ProjectConfiguration.id == configuration_id,
                ProjectConfiguration.tenant_id == tenant_id,
                ProjectConfiguration.project_id == project_id,
                ProjectConfiguration.kind == kind.value,
            )
        )
        if saved is None:
            raise LookupError("configuration not found")
        await session.delete(saved)
        await session.flush()
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="configuration.delete",
            resource_type=f"{kind.value}_configuration",
            resource_id=str(configuration_id),
            metadata={"name": saved.name, "sourceRef": saved.source_ref},
        )

    def validate(
        self,
        *,
        kind: ConfigurationKind,
        name: str,
        source_ref: str,
        configuration: dict[str, Any],
    ) -> None:
        if not name:
            raise ValueError("configuration name is required")
        if not source_ref:
            raise ValueError("source reference is required")
        if not configuration:
            raise ValueError("configuration cannot be empty")
        if kind is ConfigurationKind.AGENT:
            if source_ref != "inline/agno" and self._registry.resolve_agent(source_ref) is None:
                raise ValueError("agent source is not present in the registry snapshot")
        elif kind is ConfigurationKind.TOOL:
            if self._registry.resolve_tool(source_ref) is None:
                raise ValueError("tool source is not present in the registry snapshot")
        elif self._registry.resolve_model(source_ref) is None:
            raise ValueError("model source is not present in the registry snapshot")
