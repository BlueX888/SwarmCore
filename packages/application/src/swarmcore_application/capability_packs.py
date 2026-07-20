from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.errors import PersistenceConflictError
from swarmcore_persistence.models import (
    CapabilityPack,
    CapabilityPackVersion,
    Evaluation,
    IdempotencyKey,
    Project,
    ProjectCapabilityBinding,
    Strategy,
    StrategyVersion,
)
from swarmcore_persistence.repositories import canonical_hash
from swarmcore_registry import (
    CapabilityPackManifest,
    CapabilityReferenceCatalog,
    builtin_registry,
    hash_manifest,
    normalize_manifest,
    resolve_manifest,
)

from .capability_center import CapabilityCenterService
from .services import StrategyService


class CapabilityPackReadinessError(ValueError):
    def __init__(self, blockers: list[dict[str, Any]]) -> None:
        super().__init__("CAPABILITY_PACK_NOT_READY")
        self.blockers = blockers


class CapabilityPackDependencyError(ValueError):
    def __init__(
        self,
        *,
        strategy_ref: str,
        declared_agents: set[str],
        actual_agents: set[str],
        declared_tools: set[str],
        actual_tools: set[str],
    ) -> None:
        super().__init__("CAPABILITY_PACK_DEPENDENCY_MISMATCH")
        self.strategy_ref = strategy_ref
        self.declared_agents = declared_agents
        self.actual_agents = actual_agents
        self.declared_tools = declared_tools
        self.actual_tools = actual_tools


class CapabilityPackDeleteError(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


class CapabilityPackService:
    def __init__(
        self,
        catalog: CapabilityReferenceCatalog,
        *,
        trusted_manifests: tuple[dict[str, Any], ...] = (),
        trusted_strategies: Mapping[str, dict[str, Any]] | None = None,
    ) -> None:
        self._catalog = catalog
        self._trusted_manifests = trusted_manifests
        self._trusted_strategies = dict(trusted_strategies or {})
        self._strategies = StrategyService()
        self._audit = AuditRepository()
        self._readiness: CapabilityCenterService | None = None
        self._environment = "development"

    def attach_readiness(
        self, capability_center: CapabilityCenterService, *, environment: str
    ) -> None:
        self._readiness = capability_center
        self._environment = environment

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
        strategy_version_id: UUID | None = None,
    ) -> CapabilityPackVersion:
        strategy_ref = str(manifest.get("spec", {}).get("strategies", {}).get("execute", ""))
        catalog = self._catalog
        if strategy_version_id is not None:
            registry = builtin_registry()
            catalog = CapabilityReferenceCatalog.from_iterable(
                (
                    *self._catalog.references,
                    strategy_ref,
                    *(item.ref for item in registry.agents),
                    *(item.ref for item in registry.tools),
                    *(item.ref for item in registry.models),
                )
            )
        parsed, resolved = resolve_manifest(manifest, catalog)
        strategy_version: StrategyVersion | None = None
        raw_strategy: dict[str, Any] | None = None
        if strategy_version_id is not None:
            selected = await session.scalar(
                select(StrategyVersion)
                .join(Strategy, Strategy.id == StrategyVersion.strategy_id)
                .where(
                    StrategyVersion.id == strategy_version_id,
                    StrategyVersion.tenant_id == tenant_id,
                    StrategyVersion.lifecycle.in_({"PUBLISHED", "TRUSTED"}),
                    Strategy.project_id == project_id,
                )
            )
            if selected is None:
                raise LookupError("published strategy version not found")
            if parsed.spec.strategies.execute.rsplit("@", 1)[-1] != str(selected.version):
                raise ValueError("CAPABILITY_STRATEGY_VERSION_MISMATCH")
            strategy_version = selected
            strategy_snapshot = self._strategy_version_snapshot(
                parsed.spec.strategies.execute,
                selected,
            )
        else:
            raw_strategy = self.strategy_definition(parsed.spec.strategies.execute)
            strategy_snapshot = self._strategy_snapshot(parsed.spec.strategies.execute)
        declared_agents = set(parsed.spec.agents)
        actual_agents = set(strategy_snapshot["agents"])
        declared_tools = set(parsed.spec.tools)
        actual_tools = set(strategy_snapshot["tools"])
        if declared_agents != actual_agents or declared_tools != actual_tools:
            raise CapabilityPackDependencyError(
                strategy_ref=parsed.spec.strategies.execute,
                declared_agents=declared_agents,
                actual_agents=actual_agents,
                declared_tools=declared_tools,
                actual_tools=actual_tools,
            )
        if strategy_version is None:
            if raw_strategy is None:
                raise RuntimeError("capability pack strategy definition is missing")
            strategy_version = await self._strategies.ensure_trusted_version(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                reference=parsed.spec.strategies.execute,
                raw_spec=raw_strategy,
                registry_snapshot=str(strategy_snapshot["registrySnapshot"]),
                policy_revision="capability-pack-publish",
                actor=actor,
            )
            strategy_snapshot["strategyVersionId"] = str(strategy_version.id)
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
            dependency_snapshot={
                "references": resolved,
                "strategy": strategy_snapshot,
            },
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

    def strategy_definition(self, reference: str) -> dict[str, Any]:
        strategy = self._trusted_strategies.get(reference)
        if strategy is None:
            raise ValueError(f"CAPABILITY_STRATEGY_MISSING: {reference}")
        return deepcopy(strategy)

    def _strategy_snapshot(self, reference: str) -> dict[str, Any]:
        raw_spec = self.strategy_definition(reference)
        _, plan = self._strategies.compile(
            raw_spec,
            registry_snapshot=builtin_registry().snapshot_id,
            policy_revision="capability-pack-publish",
        )
        agents = sorted(
            str(value["registryRef"])
            for value in plan.resolved_agents.values()
            if value.get("registryRef") is not None
        )
        return {
            "ref": reference,
            "specHash": plan.spec_hash,
            "planHash": plan.plan_hash,
            "registrySnapshot": plan.registry_snapshot,
            "agents": agents,
            "models": sorted(plan.resolved_models),
            "tools": sorted(plan.resolved_tools),
        }

    @staticmethod
    def _strategy_version_snapshot(
        reference: str,
        version: StrategyVersion,
    ) -> dict[str, Any]:
        plan = version.plan
        resolved_agents = plan.get("resolved_agents", {})
        if not isinstance(resolved_agents, dict):
            raise ValueError("published strategy plan has invalid Agent dependencies")
        agents = sorted(
            str(value["registryRef"])
            for value in resolved_agents.values()
            if isinstance(value, dict) and value.get("registryRef") is not None
        )
        resolved_models = plan.get("resolved_models", {})
        resolved_tools = plan.get("resolved_tools", {})
        if not isinstance(resolved_models, dict) or not isinstance(resolved_tools, dict):
            raise ValueError("published strategy plan has invalid resource dependencies")
        agent_tools: set[str] = set()
        for value in resolved_agents.values():
            tools = value.get("tools", []) if isinstance(value, dict) else []
            if isinstance(tools, list):
                agent_tools.update(tool for tool in tools if isinstance(tool, str))
        return {
            "ref": reference,
            "strategyVersionId": str(version.id),
            "specHash": str(plan.get("spec_hash", "")),
            "planHash": version.plan_hash,
            "registrySnapshot": str(plan.get("registry_snapshot", "")),
            "agents": agents,
            "models": sorted(resolved_models),
            "tools": sorted({*resolved_tools, *agent_tools}),
        }

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
        blockers = await self.blockers_for_version(
            tenant_id=tenant_id,
            project_id=project_id,
            version=version,
        )
        if blockers:
            await self._audit.append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id=actor,
                action="capability-pack.enable-rejected",
                resource_type="capability_pack_version",
                resource_id=str(version.id),
                outcome="DENIED",
                metadata={"blockers": blockers, "contentHash": version.content_hash},
            )
            raise CapabilityPackReadinessError(blockers)
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

    async def delete_version(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        version_id: UUID,
        actor: str,
    ) -> None:
        project_exists = await session.scalar(
            select(Project.id).where(
                Project.id == project_id,
                Project.tenant_id == tenant_id,
            )
        )
        if project_exists is None:
            raise LookupError("project not found")
        version = await session.scalar(
            select(CapabilityPackVersion)
            .where(
                CapabilityPackVersion.id == version_id,
                CapabilityPackVersion.tenant_id == tenant_id,
            )
            .with_for_update()
        )
        if version is None:
            raise LookupError("能力包版本不存在或已被删除。")
        active_binding = await session.scalar(
            select(ProjectCapabilityBinding.id)
            .where(
                ProjectCapabilityBinding.tenant_id == tenant_id,
                ProjectCapabilityBinding.pack_version_id == version_id,
                ProjectCapabilityBinding.status.in_({"ENABLED", "DEGRADED"}),
            )
            .limit(1)
        )
        if active_binding is not None:
            raise CapabilityPackDeleteError(
                "CAPABILITY_PACK_ENABLED",
                "能力包版本仍处于启用状态。请先停用后再删除。",
            )
        evaluation_exists = await session.scalar(
            select(Evaluation.id)
            .where(
                Evaluation.tenant_id == tenant_id,
                Evaluation.capability_pack_version_id == version_id,
            )
            .limit(1)
        )
        if evaluation_exists is not None:
            raise CapabilityPackDeleteError(
                "CAPABILITY_PACK_HAS_EVALUATIONS",
                "能力包版本仍有历史评估引用。无法删除。",
            )
        await session.execute(
            delete(ProjectCapabilityBinding).where(
                ProjectCapabilityBinding.tenant_id == tenant_id,
                ProjectCapabilityBinding.pack_version_id == version_id,
            )
        )
        pack_id = version.pack_id
        content_hash = version.content_hash
        pack_version = version.version
        await session.delete(version)
        await session.flush()
        remaining = await session.scalar(
            select(func.count())
            .select_from(CapabilityPackVersion)
            .where(
                CapabilityPackVersion.tenant_id == tenant_id,
                CapabilityPackVersion.pack_id == pack_id,
            )
        )
        if remaining == 0:
            pack = await session.scalar(
                select(CapabilityPack).where(
                    CapabilityPack.id == pack_id,
                    CapabilityPack.tenant_id == tenant_id,
                )
            )
            if pack is not None:
                await session.delete(pack)
                await session.flush()
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="capability-pack.delete",
            resource_type="capability_pack_version",
            resource_id=str(version_id),
            metadata={"version": pack_version, "contentHash": content_hash},
        )

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
                (ProjectCapabilityBinding.pack_version_id == CapabilityPackVersion.id)
                & (ProjectCapabilityBinding.tenant_id == tenant_id)
                & (ProjectCapabilityBinding.project_id == project_id),
            )
            .where(CapabilityPack.tenant_id == tenant_id)
            .order_by(CapabilityPack.name, CapabilityPackVersion.version)
        )
        result: list[
            tuple[CapabilityPack, CapabilityPackVersion, ProjectCapabilityBinding | None]
        ] = list(rows.tuples())
        for _, version, binding in result:
            if binding is None or binding.status not in {"ENABLED", "DEGRADED"}:
                continue
            blockers = await self.blockers_for_version(
                tenant_id=tenant_id,
                project_id=project_id,
                version=version,
            )
            next_status = "DEGRADED" if blockers else "ENABLED"
            if binding.status == next_status:
                continue
            previous = binding.status
            binding.status = next_status
            await session.flush()
            await self._audit.append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                actor_id="capability-readiness-reconciler",
                action=(
                    "capability-pack.degraded"
                    if next_status == "DEGRADED"
                    else "capability-pack.recovered"
                ),
                resource_type="capability_pack_version",
                resource_id=str(version.id),
                metadata={"from": previous, "to": next_status, "blockers": blockers},
            )
        return result

    async def blockers_for_version(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        version: CapabilityPackVersion,
    ) -> list[dict[str, Any]]:
        manifest = CapabilityPackManifest.model_validate(version.manifest)
        required = (*manifest.spec.agents, *manifest.spec.tools)
        if not required:
            return []
        if self._readiness is None:
            return [
                {"ref": reference, "reasons": ["DEPENDENCY_NOT_READY"]}
                for reference in required
            ]
        summaries = {
            item.ref: item
            for item in await self._readiness.list(
                tenant_id=tenant_id,
                project_id=project_id,
                environment=self._environment,
            )
        }
        blockers: list[dict[str, Any]] = []
        for reference in required:
            summary = summaries.get(reference)
            if summary is None:
                blockers.append(
                    {"ref": reference, "reasons": ["DEPENDENCY_NOT_READY"]}
                )
            elif summary.readiness.status.value != "READY":
                blockers.append(
                    {
                        "ref": reference,
                        "reasons": [reason.code.value for reason in summary.readiness.reasons],
                    }
                )
        return blockers

    async def resolve_enabled(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_item_type: str,
    ) -> tuple[CapabilityPackVersion, CapabilityPackManifest, ProjectCapabilityBinding]:
        rows = list(
            (
                await session.execute(
                    select(CapabilityPackVersion, ProjectCapabilityBinding)
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
            ).tuples()
        )
        matches = [
            (version, CapabilityPackManifest.model_validate(version.manifest), binding)
            for version, binding in rows
            if version.manifest.get("spec", {}).get("workItemType") == work_item_type
        ]
        if not matches:
            raise ValueError("CAPABILITY_PACK_NOT_ENABLED")
        if len(matches) > 1:
            raise ValueError("CAPABILITY_PACK_AMBIGUOUS")
        return matches[0]
