from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.errors import PersistenceConflictError
from swarmcore_persistence.models import (
    CapabilityPack,
    CapabilityPackVersion,
    IdempotencyKey,
    Project,
    ProjectCapabilityBinding,
)
from swarmcore_persistence.repositories import canonical_hash
from swarmcore_registry import (
    CapabilityPackManifest,
    CapabilityReferenceCatalog,
    hash_manifest,
    normalize_manifest,
    resolve_manifest,
)


class CapabilityPackService:
    def __init__(
        self,
        catalog: CapabilityReferenceCatalog,
        *,
        trusted_manifests: tuple[dict[str, Any], ...] = (),
    ) -> None:
        self._catalog = catalog
        self._trusted_manifests = trusted_manifests
        self._audit = AuditRepository()

    async def ensure_trusted(
        self, session: AsyncSession, *, tenant_id: UUID, project_id: UUID
    ) -> list[CapabilityPackVersion]:
        project_exists = await session.scalar(
            select(Project.id).where(
                Project.id == project_id,
                Project.tenant_id == tenant_id,
            )
        )
        if project_exists is None:
            raise LookupError("project not found")
        return [
            await self.publish(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                manifest=manifest,
                actor="trusted-manifest-loader",
            )
            for manifest in self._trusted_manifests
        ]

    async def publish(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        manifest: dict[str, Any],
        actor: str,
    ) -> CapabilityPackVersion:
        parsed, resolved = resolve_manifest(manifest, self._catalog)
        normalized = normalize_manifest(parsed)
        digest = hash_manifest(parsed)
        pack = await session.scalar(
            select(CapabilityPack).where(
                CapabilityPack.tenant_id == tenant_id,
                CapabilityPack.name == parsed.metadata.name,
            )
        )
        if pack is None:
            pack = CapabilityPack(
                tenant_id=tenant_id,
                name=parsed.metadata.name,
                lifecycle="ACTIVE",
            )
            session.add(pack)
            await session.flush()
        existing = await session.scalar(
            select(CapabilityPackVersion).where(
                CapabilityPackVersion.pack_id == pack.id,
                CapabilityPackVersion.version == parsed.metadata.version,
            )
        )
        if existing is not None:
            if existing.content_hash != digest:
                raise PersistenceConflictError(
                    "capability pack version is immutable and has different content"
                )
            return existing
        saved = CapabilityPackVersion(
            tenant_id=tenant_id,
            pack_id=pack.id,
            version=parsed.metadata.version,
            manifest=normalized,
            dependency_snapshot={"references": resolved},
            content_hash=digest,
            created_by=actor,
        )
        session.add(saved)
        await session.flush()
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="capability-pack.publish",
            resource_type="capability_pack_version",
            resource_id=str(saved.id),
            metadata={"contentHash": digest, "version": saved.version},
        )
        return saved

    async def enable(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        version_id: UUID,
        configuration: dict[str, Any],
        idempotency_key: str,
        actor: str,
    ) -> ProjectCapabilityBinding:
        version = await session.scalar(
            select(CapabilityPackVersion).where(
                CapabilityPackVersion.id == version_id,
                CapabilityPackVersion.tenant_id == tenant_id,
            )
        )
        if version is None:
            raise LookupError("capability pack version not found")
        request_hash = canonical_hash(
            {"versionId": str(version_id), "configuration": configuration}
        )
        operation = "capability-pack.enable"
        existing_key = await session.get(
            IdempotencyKey, (tenant_id, project_id, operation, idempotency_key)
        )
        if existing_key is not None:
            if existing_key.request_hash != request_hash:
                raise ValueError("IDEMPOTENCY_KEY_REUSED")
            existing_binding = await session.get(
                ProjectCapabilityBinding, existing_key.response_ref
            )
            if existing_binding is None:
                raise RuntimeError("capability binding idempotency record is invalid")
            return existing_binding
        binding = await session.scalar(
            select(ProjectCapabilityBinding)
            .where(
                ProjectCapabilityBinding.tenant_id == tenant_id,
                ProjectCapabilityBinding.project_id == project_id,
                ProjectCapabilityBinding.pack_id == version.pack_id,
            )
            .with_for_update()
        )
        if binding is None:
            binding = ProjectCapabilityBinding(
                tenant_id=tenant_id,
                project_id=project_id,
                pack_id=version.pack_id,
                pack_version_id=version.id,
                status="ENABLED",
                configuration=configuration,
                enabled_by=actor,
            )
            session.add(binding)
        else:
            binding.pack_version_id = version.id
            binding.status = "ENABLED"
            binding.configuration = configuration
            binding.enabled_by = actor
        await session.flush()
        session.add(
            IdempotencyKey(
                tenant_id=tenant_id,
                project_id=project_id,
                operation=operation,
                key=idempotency_key,
                request_hash=request_hash,
                response_ref=binding.id,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="capability-pack.enable",
            resource_type="capability_pack_version",
            resource_id=str(version.id),
            metadata={"contentHash": version.content_hash},
        )
        return binding

    async def disable(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        version_id: UUID,
        idempotency_key: str,
        actor: str,
    ) -> ProjectCapabilityBinding:
        binding = await session.scalar(
            select(ProjectCapabilityBinding)
            .where(
                ProjectCapabilityBinding.tenant_id == tenant_id,
                ProjectCapabilityBinding.project_id == project_id,
                ProjectCapabilityBinding.pack_version_id == version_id,
            )
            .with_for_update()
        )
        if binding is None:
            raise LookupError("enabled capability pack version not found")
        request_hash = canonical_hash({"versionId": str(version_id)})
        operation = "capability-pack.disable"
        existing_key = await session.get(
            IdempotencyKey, (tenant_id, project_id, operation, idempotency_key)
        )
        if existing_key is not None:
            if existing_key.request_hash != request_hash:
                raise ValueError("IDEMPOTENCY_KEY_REUSED")
            return binding
        binding.status = "DISABLED"
        await session.flush()
        session.add(
            IdempotencyKey(
                tenant_id=tenant_id,
                project_id=project_id,
                operation=operation,
                key=idempotency_key,
                request_hash=request_hash,
                response_ref=binding.id,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="capability-pack.disable",
            resource_type="capability_pack_version",
            resource_id=str(version_id),
        )
        return binding

    async def list_project(
        self, session: AsyncSession, *, tenant_id: UUID, project_id: UUID
    ) -> list[tuple[CapabilityPack, CapabilityPackVersion, ProjectCapabilityBinding | None]]:
        rows = await session.execute(
            select(CapabilityPack, CapabilityPackVersion, ProjectCapabilityBinding)
            .join(
                CapabilityPackVersion,
                CapabilityPackVersion.pack_id == CapabilityPack.id,
            )
            .outerjoin(
                ProjectCapabilityBinding,
                (ProjectCapabilityBinding.pack_id == CapabilityPack.id)
                & (ProjectCapabilityBinding.project_id == project_id),
            )
            .where(CapabilityPack.tenant_id == tenant_id)
            .order_by(CapabilityPack.name, CapabilityPackVersion.version)
        )
        return list(rows.tuples())

    async def resolve_enabled(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_item_type: str,
    ) -> tuple[CapabilityPackVersion, CapabilityPackManifest]:
        versions = list(
            await session.scalars(
                select(CapabilityPackVersion)
                .join(
                    ProjectCapabilityBinding,
                    ProjectCapabilityBinding.pack_version_id == CapabilityPackVersion.id,
                )
                .where(
                    ProjectCapabilityBinding.tenant_id == tenant_id,
                    ProjectCapabilityBinding.project_id == project_id,
                    ProjectCapabilityBinding.status == "ENABLED",
                )
            )
        )
        matches = [
            (version, CapabilityPackManifest.model_validate(version.manifest))
            for version in versions
            if version.manifest.get("spec", {}).get("workItemType") == work_item_type
        ]
        if not matches:
            raise ValueError("CAPABILITY_PACK_NOT_ENABLED")
        if len(matches) > 1:
            raise ValueError("CAPABILITY_PACK_AMBIGUOUS")
        return matches[0]
