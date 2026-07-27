from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jsonschema import Draft202012Validator, ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_compiler import Compiler, ExecutionPlan
from swarmcore_domain import uuid7
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.errors import PersistenceConflictError
from swarmcore_persistence.models import (
    CapabilityPackVersion,
    Evaluation,
    IdempotencyKey,
    Run,
    Strategy,
    StrategyDraft,
    StrategyVersion,
)
from swarmcore_persistence.repositories import EventRepository, RunCommandRepository, canonical_hash
from swarmcore_registry import builtin_registry
from swarmcore_spec import SwarmStrategy

_DELETABLE_LIFECYCLES = frozenset({"ACTIVE"})
_SYSTEM_MANAGED_LIFECYCLES = frozenset({"TRUSTED", "EPHEMERAL"})


@dataclass(frozen=True, slots=True)
class StrategyDeleteBlocker:
    code: str
    count: int
    message: str


@dataclass(frozen=True, slots=True)
class StrategyDeleteImpact:
    strategy_id: UUID
    deletable: bool
    blockers: tuple[StrategyDeleteBlocker, ...]


class StrategyDeleteError(ValueError):
    def __init__(
        self, blockers: tuple[StrategyDeleteBlocker, ...] | list[StrategyDeleteBlocker]
    ) -> None:
        self.code = "STRATEGY_DELETE_BLOCKED"
        self.blockers = tuple(blockers)
        self.detail = "策略已有发布版本或历史使用记录,不能删除。"
        super().__init__(self.code)


class StrategyService:
    def __init__(self, compiler: Compiler | None = None) -> None:
        self.compiler = compiler or Compiler()
        self._audit = AuditRepository()

    def compile(
        self, raw_spec: dict[str, Any], *, registry_snapshot: str, policy_revision: str
    ) -> tuple[SwarmStrategy, ExecutionPlan]:
        strategy = SwarmStrategy.model_validate(raw_spec)
        plan = self.compiler.compile(
            strategy,
            registry_snapshot=registry_snapshot,
            policy_revision=policy_revision,
        )
        return strategy, plan

    async def ensure_trusted_version(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        reference: str,
        raw_spec: dict[str, Any],
        registry_snapshot: str,
        policy_revision: str,
        actor: str,
    ) -> StrategyVersion:
        if not reference.startswith("strategy://") or "@" not in reference:
            raise ValueError(f"invalid immutable strategy reference: {reference}")
        resource, version_text = reference.removeprefix("strategy://").rsplit("@", 1)
        try:
            version_number = int(version_text)
        except ValueError as exc:
            raise ValueError(f"strategy reference version must be an integer: {reference}") from exc
        if version_number < 1:
            raise ValueError(f"strategy reference version must be positive: {reference}")
        name = f"trusted-{resource.replace('/', '-')}"
        spec, plan = self.compile(
            raw_spec,
            registry_snapshot=registry_snapshot,
            policy_revision=policy_revision,
        )
        strategy = await session.scalar(
            select(Strategy)
            .where(
                Strategy.tenant_id == tenant_id,
                Strategy.project_id == project_id,
                Strategy.name == name,
            )
            .with_for_update()
        )
        if strategy is None:
            strategy = Strategy(
                tenant_id=tenant_id,
                project_id=project_id,
                name=name,
                lifecycle="TRUSTED",
            )
            session.add(strategy)
            await session.flush()
        existing = await session.scalar(
            select(StrategyVersion).where(
                StrategyVersion.tenant_id == tenant_id,
                StrategyVersion.strategy_id == strategy.id,
                StrategyVersion.version == version_number,
            )
        )
        if existing is not None:
            if canonical_hash(existing.raw_spec) != canonical_hash(raw_spec):
                raise PersistenceConflictError(
                    "trusted strategy version is immutable and has different content"
                )
            return existing
        saved = StrategyVersion(
            tenant_id=tenant_id,
            strategy_id=strategy.id,
            version=version_number,
            lifecycle="TRUSTED",
            raw_spec=raw_spec,
            normalized_spec=spec.model_dump(mode="json", by_alias=True, exclude_none=True),
            plan=plan.model_dump(mode="json", by_alias=True),
            plan_hash=plan.plan_hash,
            schema_version=spec.api_version,
            runtime_version=plan.runtime_version,
        )
        session.add(saved)
        await session.flush()
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="strategy.trusted-register",
            resource_type="strategy_version",
            resource_id=str(saved.id),
            policy_revision=policy_revision,
            metadata={"reference": reference, "planHash": saved.plan_hash},
        )
        return saved

    async def create_draft(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        name: str,
        raw_spec: dict[str, Any],
        actor: str,
        editor_state: dict[str, Any] | None = None,
    ) -> tuple[Strategy, StrategyDraft]:
        SwarmStrategy.model_validate(raw_spec)
        existing = await session.scalar(
            select(Strategy.id).where(
                Strategy.tenant_id == tenant_id,
                Strategy.project_id == project_id,
                Strategy.name == name,
            )
        )
        if existing is not None:
            raise PersistenceConflictError("strategy name already exists in this project")
        strategy = Strategy(tenant_id=tenant_id, project_id=project_id, name=name)
        session.add(strategy)
        await session.flush()
        draft = StrategyDraft(
            tenant_id=tenant_id,
            strategy_id=strategy.id,
            raw_spec=raw_spec,
            editor_state=editor_state or {},
            diagnostics=[],
            updated_by=actor,
        )
        session.add(draft)
        await session.flush()
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="strategy.create",
            resource_type="strategy",
            resource_id=str(strategy.id),
        )
        return strategy, draft

    async def publish(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        strategy_id: UUID,
        draft_id: UUID,
        registry_snapshot: str,
        policy_revision: str,
        actor: str = "system",
    ) -> StrategyVersion:
        strategy = await session.scalar(
            select(Strategy)
            .where(Strategy.id == strategy_id, Strategy.tenant_id == tenant_id)
            .with_for_update()
        )
        if strategy is None:
            raise LookupError("strategy not found")
        draft = await session.scalar(
            select(StrategyDraft).where(
                StrategyDraft.id == draft_id,
                StrategyDraft.strategy_id == strategy_id,
                StrategyDraft.tenant_id == tenant_id,
            )
        )
        if draft is None:
            raise LookupError("draft not found")
        spec, plan = self.compile(
            draft.raw_spec,
            registry_snapshot=registry_snapshot,
            policy_revision=policy_revision,
        )
        current = await session.scalar(
            select(func.max(StrategyVersion.version)).where(
                StrategyVersion.strategy_id == strategy_id
            )
        )
        version = StrategyVersion(
            tenant_id=tenant_id,
            strategy_id=strategy_id,
            version=(current or 0) + 1,
            raw_spec=draft.raw_spec,
            normalized_spec=spec.model_dump(mode="json", by_alias=True, exclude_none=True),
            plan=plan.model_dump(mode="json", by_alias=True),
            plan_hash=plan.plan_hash,
            schema_version=spec.api_version,
            runtime_version=plan.runtime_version,
        )
        session.add(version)
        await session.flush()
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=strategy.project_id,
            actor_id=actor,
            action="strategy.publish",
            resource_type="strategy",
            resource_id=str(strategy.id),
            policy_revision=policy_revision,
            metadata={"version": version.version, "planHash": version.plan_hash},
        )
        return version

    async def update_draft(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        strategy_id: UUID,
        draft_id: UUID,
        expected_revision: int,
        raw_spec: dict[str, Any],
        actor: str,
        editor_state: dict[str, Any] | None = None,
    ) -> StrategyDraft:
        SwarmStrategy.model_validate(raw_spec)
        draft = await session.scalar(
            select(StrategyDraft)
            .where(
                StrategyDraft.id == draft_id,
                StrategyDraft.strategy_id == strategy_id,
                StrategyDraft.tenant_id == tenant_id,
            )
            .with_for_update()
        )
        if draft is None:
            raise LookupError("draft not found")
        if draft.revision != expected_revision:
            raise PersistenceConflictError(
                f"draft revision is {draft.revision}, expected {expected_revision}"
            )
        draft.raw_spec = raw_spec
        if editor_state is not None:
            draft.editor_state = editor_state
        draft.revision += 1
        draft.updated_by = actor
        draft.updated_at = datetime.now(UTC)
        draft.diagnostics = []
        await session.flush()
        strategy = await session.get(Strategy, strategy_id)
        if strategy is None:
            raise LookupError("strategy not found")
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=strategy.project_id,
            actor_id=actor,
            action="strategy.update",
            resource_type="strategy",
            resource_id=strategy_id.hex,
            metadata={"revision": draft.revision},
        )
        return draft

    async def get_delete_impact(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        strategy_id: UUID,
    ) -> StrategyDeleteImpact:
        strategy = await session.scalar(
            select(Strategy).where(
                Strategy.id == strategy_id,
                Strategy.tenant_id == tenant_id,
                Strategy.project_id == project_id,
            )
        )
        if strategy is None:
            raise LookupError("strategy not found")
        blockers = await self._collect_delete_blockers(
            session,
            tenant_id=tenant_id,
            strategy=strategy,
        )
        return StrategyDeleteImpact(
            strategy_id=strategy.id,
            deletable=len(blockers) == 0,
            blockers=blockers,
        )

    async def delete(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        strategy_id: UUID,
        actor: str,
    ) -> None:
        strategy = await session.scalar(
            select(Strategy)
            .where(
                Strategy.id == strategy_id,
                Strategy.tenant_id == tenant_id,
                Strategy.project_id == project_id,
            )
            .with_for_update()
        )
        if strategy is None:
            raise LookupError("strategy not found")
        blockers = await self._collect_delete_blockers(
            session,
            tenant_id=tenant_id,
            strategy=strategy,
        )
        if blockers:
            raise StrategyDeleteError(blockers)
        draft_count = int(
            await session.scalar(
                select(func.count())
                .select_from(StrategyDraft)
                .where(
                    StrategyDraft.tenant_id == tenant_id,
                    StrategyDraft.strategy_id == strategy.id,
                )
            )
            or 0
        )
        lifecycle = strategy.lifecycle
        name = strategy.name
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="strategy.delete",
            resource_type="strategy",
            resource_id=str(strategy.id),
            metadata={
                "name": name,
                "lifecycle": lifecycle,
                "draftCount": draft_count,
            },
        )
        await session.delete(strategy)
        await session.flush()

    async def _collect_delete_blockers(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        strategy: Strategy,
    ) -> tuple[StrategyDeleteBlocker, ...]:
        version_count = int(
            await session.scalar(
                select(func.count())
                .select_from(StrategyVersion)
                .where(
                    StrategyVersion.tenant_id == tenant_id,
                    StrategyVersion.strategy_id == strategy.id,
                )
            )
            or 0
        )
        version_ids = list(
            await session.scalars(
                select(StrategyVersion.id).where(
                    StrategyVersion.tenant_id == tenant_id,
                    StrategyVersion.strategy_id == strategy.id,
                )
            )
        )
        run_count = 0
        assessment_count = 0
        business_work_count = 0
        if version_ids:
            run_count = int(
                await session.scalar(
                    select(func.count())
                    .select_from(Run)
                    .where(
                        Run.tenant_id == tenant_id,
                        Run.strategy_version_id.in_(version_ids),
                    )
                )
                or 0
            )
            assessment_count = int(
                await session.scalar(
                    select(func.count())
                    .select_from(Evaluation)
                    .where(
                        Evaluation.tenant_id == tenant_id,
                        Evaluation.strategy_version_id.in_(version_ids),
                    )
                )
                or 0
            )
            version_id_texts = [str(item) for item in version_ids]
            business_work_count = int(
                await session.scalar(
                    select(func.count())
                    .select_from(CapabilityPackVersion)
                    .where(
                        CapabilityPackVersion.tenant_id == tenant_id,
                        CapabilityPackVersion.dependency_snapshot["strategy"][
                            "strategyVersionId"
                        ].astext.in_(version_id_texts),
                    )
                )
                or 0
            )
        return self.build_delete_blockers(
            lifecycle=strategy.lifecycle,
            version_count=version_count,
            run_count=run_count,
            assessment_count=assessment_count,
            business_work_count=business_work_count,
        )

    @staticmethod
    def build_delete_blockers(
        *,
        lifecycle: str,
        version_count: int,
        run_count: int,
        assessment_count: int,
        business_work_count: int,
    ) -> tuple[StrategyDeleteBlocker, ...]:
        blockers: list[StrategyDeleteBlocker] = []
        if lifecycle in _SYSTEM_MANAGED_LIFECYCLES or lifecycle not in _DELETABLE_LIFECYCLES:
            blockers.append(
                StrategyDeleteBlocker(
                    code="STRATEGY_DELETE_NOT_ALLOWED",
                    count=1,
                    message=(
                        "系统管理策略(TRUSTED/EPHEMERAL 等)不能通过项目策略页面删除"
                        if lifecycle in _SYSTEM_MANAGED_LIFECYCLES
                        else f"策略生命周期为 {lifecycle},不允许删除"
                    ),
                )
            )
        if version_count > 0:
            blockers.append(
                StrategyDeleteBlocker(
                    code="STRATEGY_HAS_PUBLISHED_VERSIONS",
                    count=version_count,
                    message=f"策略存在 {version_count} 个已发布版本",
                )
            )
        if run_count > 0:
            blockers.append(
                StrategyDeleteBlocker(
                    code="STRATEGY_IN_USE_BY_RUN",
                    count=run_count,
                    message=f"策略已被 {run_count} 次运行引用",
                )
            )
        if assessment_count > 0:
            blockers.append(
                StrategyDeleteBlocker(
                    code="STRATEGY_IN_USE_BY_ASSESSMENT",
                    count=assessment_count,
                    message=f"策略已被 {assessment_count} 次评估/考核引用",
                )
            )
        if business_work_count > 0:
            blockers.append(
                StrategyDeleteBlocker(
                    code="STRATEGY_IN_USE_BY_BUSINESS_WORK",
                    count=business_work_count,
                    message=f"策略被 {business_work_count} 个业务工作/能力包依赖快照引用",
                )
            )
        return tuple(blockers)


class RunService:
    def __init__(self) -> None:
        self._commands = RunCommandRepository()
        self.events = EventRepository()
        self._audit = AuditRepository()

    async def create(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        strategy_version_id: UUID,
        input_data: dict[str, Any],
        idempotency_key: str,
        initiated_by: str = "system",
        submitted_scopes: tuple[str, ...] = (),
        auth_context_hash: str = "unknown",
    ) -> tuple[Run, Any]:
        request_hash = canonical_hash(
            {"strategyVersionId": str(strategy_version_id), "input": input_data}
        )
        existing = await self._existing(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if existing is not None:
            return existing

        version = await session.scalar(
            select(StrategyVersion)
            .join(Strategy, Strategy.id == StrategyVersion.strategy_id)
            .where(
                StrategyVersion.id == strategy_version_id,
                StrategyVersion.tenant_id == tenant_id,
                Strategy.project_id == project_id,
            )
        )
        if version is None:
            raise LookupError("strategy version not found")
        return await self._create_for_version(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            version=version,
            input_data=input_data,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            initiated_by=initiated_by,
            submitted_scopes=submitted_scopes,
            auth_context_hash=auth_context_hash,
            policy_revision=str(version.plan.get("policy_revision", "unknown")),
        )

    async def create_inline(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        raw_spec: dict[str, Any],
        input_data: dict[str, Any],
        idempotency_key: str,
        registry_snapshot: str = builtin_registry().snapshot_id,
        policy_revision: str = "m3",
        initiated_by: str = "system",
        submitted_scopes: tuple[str, ...] = (),
        auth_context_hash: str = "unknown",
    ) -> tuple[Run, Any]:
        request_hash = canonical_hash({"spec": raw_spec, "input": input_data})
        existing = await self._existing(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        if existing is not None:
            return existing

        spec, plan = StrategyService().compile(
            raw_spec,
            registry_snapshot=registry_snapshot,
            policy_revision=policy_revision,
        )
        strategy = Strategy(
            tenant_id=tenant_id,
            project_id=project_id,
            name=f"inline-{uuid7()}",
            lifecycle="EPHEMERAL",
        )
        session.add(strategy)
        await session.flush()
        version = StrategyVersion(
            tenant_id=tenant_id,
            strategy_id=strategy.id,
            version=1,
            lifecycle="EPHEMERAL",
            raw_spec=raw_spec,
            normalized_spec=spec.model_dump(mode="json", by_alias=True, exclude_none=True),
            plan=plan.model_dump(mode="json", by_alias=True),
            plan_hash=plan.plan_hash,
            schema_version=spec.api_version,
            runtime_version=plan.runtime_version,
        )
        session.add(version)
        await session.flush()
        return await self._create_for_version(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            version=version,
            input_data=input_data,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            initiated_by=initiated_by,
            submitted_scopes=submitted_scopes,
            auth_context_hash=auth_context_hash,
            policy_revision=policy_revision,
        )

    async def _existing(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        idempotency_key: str,
        request_hash: str,
    ) -> tuple[Run, Any] | None:
        existing_key = await session.scalar(
            select(IdempotencyKey).where(
                IdempotencyKey.tenant_id == tenant_id,
                IdempotencyKey.project_id == project_id,
                IdempotencyKey.operation == "run.create",
                IdempotencyKey.key == idempotency_key,
            )
        )
        if existing_key is not None:
            if existing_key.request_hash != request_hash:
                raise ValueError("IDEMPOTENCY_KEY_REUSED")
            run = await session.get(Run, existing_key.response_ref)
            if run is None:
                raise RuntimeError("idempotency record references a missing run")
            command = await self._commands.append(
                session,
                tenant_id=tenant_id,
                run_id=run.id,
                command_type="start",
                request_id=run.id,
                payload={},
            )
            return run, command
        return None

    async def _create_for_version(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        version: StrategyVersion,
        input_data: dict[str, Any],
        idempotency_key: str,
        request_hash: str,
        initiated_by: str,
        submitted_scopes: tuple[str, ...],
        auth_context_hash: str,
        policy_revision: str,
    ) -> tuple[Run, Any]:
        try:
            Draft202012Validator(version.plan["input_schema"]).validate(input_data)
        except ValidationError as exc:
            raise ValueError(f"RUN_INPUT_INVALID: {exc.message}") from exc

        run_id = uuid7()
        run = Run(
            id=run_id,
            tenant_id=tenant_id,
            project_id=project_id,
            strategy_version_id=version.id,
            input=input_data,
            budgets=version.plan["budget"],
            plan_hash=version.plan_hash,
            runtime_version=version.runtime_version,
            temporal_workflow_id=f"swarm:{tenant_id}:{run_id}",
            initiated_by=initiated_by,
            submitted_scopes=list(submitted_scopes),
            auth_context_hash=auth_context_hash,
            policy_revision=policy_revision,
        )
        session.add(run)
        await session.flush()
        session.add(
            IdempotencyKey(
                tenant_id=tenant_id,
                project_id=project_id,
                operation="run.create",
                key=idempotency_key,
                request_hash=request_hash,
                response_ref=run.id,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )
        command = await self._commands.append(
            session,
            tenant_id=tenant_id,
            run_id=run.id,
            command_type="start",
            request_id=run.id,
            payload={},
        )
        await self.events.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            run_id=run.id,
            transition_id=uuid7(),
            event_type="run.accepted",
            payload={},
            occurred_at=datetime.now(UTC),
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=initiated_by,
            action="run.create",
            resource_type="run",
            resource_id=str(run.id),
            run_id=run.id,
            policy_revision=policy_revision,
            metadata={"planHash": run.plan_hash},
        )
        return run, command
