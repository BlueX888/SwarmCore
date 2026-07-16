from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from jsonschema import Draft202012Validator, ValidationError
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_compiler import Compiler, ExecutionPlan
from swarmcore_domain import uuid7
from swarmcore_persistence.errors import PersistenceConflictError
from swarmcore_persistence.models import (
    IdempotencyKey,
    Run,
    Strategy,
    StrategyDraft,
    StrategyVersion,
)
from swarmcore_persistence.repositories import EventRepository, RunCommandRepository, canonical_hash
from swarmcore_spec import SwarmStrategy


class StrategyService:
    def __init__(self, compiler: Compiler | None = None) -> None:
        self.compiler = compiler or Compiler()

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
        return draft


class RunService:
    def __init__(self) -> None:
        self.commands = RunCommandRepository()
        self.events = EventRepository()

    async def create(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        strategy_version_id: UUID,
        input_data: dict[str, Any],
        idempotency_key: str,
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
        registry_snapshot: str = "inline",
        policy_revision: str = "phase2b",
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
            command = await self.commands.append(
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
        command = await self.commands.append(
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
        return run, command
