from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_domain import CapabilityKind, CapabilitySummary
from swarmcore_persistence.models import ProjectConfiguration

from .capability_center import CapabilityCenterService
from .configurations import ConfigurationKind, ProjectConfigurationService

_SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "password",
        "secret",
        "token",
        "apikey",
        "privatekey",
        "accesstoken",
        "refreshtoken",
        "clientsecret",
    }
)


class CapabilityPresetService:
    def __init__(
        self,
        capability_center: CapabilityCenterService,
        configurations: ProjectConfigurationService | None = None,
    ) -> None:
        self._center = capability_center
        self._configurations = configurations or ProjectConfigurationService()

    async def create(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        name: str,
        capability_ref: str,
        parameters: dict[str, Any],
        actor: str,
    ) -> ProjectConfiguration:
        summary = await self._require_capability(
            tenant_id, project_id, environment, capability_ref
        )
        self.validate_parameters(parameters)
        return await self._configurations.create(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            kind=self._configuration_kind(summary.kind),
            name=name,
            source_ref=summary.ref,
            configuration=parameters,
            actor=actor,
        )

    async def list(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[tuple[ProjectConfiguration, CapabilitySummary | None]], int]:
        scope = (
            ProjectConfiguration.tenant_id == tenant_id,
            ProjectConfiguration.project_id == project_id,
        )
        rows = list(
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
        summaries = {
            item.ref: item
            for item in await self._center.list(
                tenant_id=tenant_id,
                project_id=project_id,
                environment=environment,
            )
        }
        return [(row, summaries.get(row.source_ref)) for row in rows], total or 0

    async def update(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        preset_id: UUID,
        name: str,
        capability_ref: str,
        parameters: dict[str, Any],
        actor: str,
    ) -> ProjectConfiguration:
        saved = await self._get(session, tenant_id, project_id, preset_id)
        summary = await self._require_capability(
            tenant_id, project_id, environment, capability_ref
        )
        kind = self._configuration_kind(summary.kind)
        if saved.kind != kind.value:
            raise ValueError("preset capability kind cannot be changed")
        self.validate_parameters(parameters)
        return await self._configurations.update(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            kind=kind,
            configuration_id=preset_id,
            name=name,
            source_ref=summary.ref,
            configuration=parameters,
            actor=actor,
        )

    async def delete(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        preset_id: UUID,
        actor: str,
    ) -> None:
        saved = await self._get(session, tenant_id, project_id, preset_id)
        await self._configurations.delete(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            kind=ConfigurationKind(saved.kind),
            configuration_id=preset_id,
            actor=actor,
        )

    async def copy(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        preset_id: UUID,
        name: str,
        actor: str,
    ) -> ProjectConfiguration:
        saved = await self._get(session, tenant_id, project_id, preset_id)
        return await self.create(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            environment=environment,
            name=name,
            capability_ref=saved.source_ref,
            parameters=dict(saved.configuration),
            actor=actor,
        )

    async def resolve_input(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        preset_id: UUID,
        capability_ref: str,
    ) -> dict[str, Any]:
        saved = await self._get(session, tenant_id, project_id, preset_id)
        if saved.source_ref != capability_ref:
            raise ValueError("preset does not belong to the requested capability")
        self.validate_parameters(saved.configuration)
        return dict(saved.configuration)

    @classmethod
    def validate_parameters(cls, parameters: Mapping[str, Any]) -> None:
        if not parameters:
            raise ValueError("preset parameters cannot be empty")
        cls._assert_no_secrets(parameters)

    @classmethod
    def _assert_no_secrets(cls, value: Any) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                normalized = "".join(
                    character
                    for character in str(key).lower()
                    if character.isalnum()
                )
                if normalized in _SENSITIVE_KEYS:
                    raise ValueError(f"preset contains forbidden secret field: {key}")
                cls._assert_no_secrets(item)
        elif isinstance(value, list | tuple):
            for item in value:
                cls._assert_no_secrets(item)

    async def _require_capability(
        self,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        capability_ref: str,
    ) -> CapabilitySummary:
        items = await self._center.list(
            tenant_id=tenant_id,
            project_id=project_id,
            environment=environment,
        )
        summary = next((item for item in items if item.ref == capability_ref), None)
        if summary is None:
            raise LookupError("capability not found")
        return summary

    @staticmethod
    def _configuration_kind(kind: CapabilityKind) -> ConfigurationKind:
        try:
            return ConfigurationKind(kind.value)
        except ValueError as exc:
            raise ValueError("policy presets are not supported by the compatibility table") from exc

    @staticmethod
    async def _get(
        session: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
        preset_id: UUID,
    ) -> ProjectConfiguration:
        saved = await session.scalar(
            select(ProjectConfiguration).where(
                ProjectConfiguration.id == preset_id,
                ProjectConfiguration.tenant_id == tenant_id,
                ProjectConfiguration.project_id == project_id,
            )
        )
        if saved is None:
            raise LookupError("preset not found")
        return saved
