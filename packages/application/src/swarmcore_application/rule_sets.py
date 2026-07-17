from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_domain import uuid7
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.errors import PersistenceConflictError
from swarmcore_persistence.models import (
    IdempotencyKey,
    OutboxEvent,
    RuleSet,
    RuleSetDraft,
    RuleSetVersion,
)
from swarmcore_persistence.repositories import canonical_hash

from .integrity import (
    AttachmentInput,
    IntegrityResult,
    IntegrityRuleDocument,
    evaluate_integrity,
    select_unique_rule,
)


class RuleSetService:
    def __init__(self) -> None:
        self._audit = AuditRepository()

    async def create(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        name: str,
        purpose: str,
        rules: dict[str, Any],
        idempotency_key: str,
        actor: str,
    ) -> tuple[RuleSet, RuleSetDraft]:
        IntegrityRuleDocument.model_validate(rules)
        request_hash = canonical_hash({"name": name, "purpose": purpose, "rules": rules})
        existing = await self._idempotent_response(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation="rule-set.create",
            key=idempotency_key,
            request_hash=request_hash,
        )
        if existing is not None:
            rule_set = await session.get(RuleSet, existing)
            draft = await session.scalar(
                select(RuleSetDraft).where(RuleSetDraft.rule_set_id == existing)
            )
            if rule_set is None or draft is None:
                raise RuntimeError("rule set idempotency record is invalid")
            return rule_set, draft
        rule_set = RuleSet(
            tenant_id=tenant_id,
            project_id=project_id,
            name=name,
            purpose=purpose,
        )
        session.add(rule_set)
        await session.flush()
        draft = RuleSetDraft(
            tenant_id=tenant_id,
            project_id=project_id,
            rule_set_id=rule_set.id,
            revision=1,
            rules=rules,
            updated_by=actor,
        )
        session.add(draft)
        await session.flush()
        await self._record_idempotency(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation="rule-set.create",
            key=idempotency_key,
            request_hash=request_hash,
            response_ref=rule_set.id,
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="rule-set.create",
            resource_type="rule_set",
            resource_id=str(rule_set.id),
        )
        return rule_set, draft

    async def update_draft(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        draft_id: UUID,
        expected_revision: int,
        rules: dict[str, Any],
        idempotency_key: str,
        actor: str,
    ) -> RuleSetDraft:
        IntegrityRuleDocument.model_validate(rules)
        request_hash = canonical_hash(
            {"draftId": str(draft_id), "expectedRevision": expected_revision, "rules": rules}
        )
        operation = f"rule-set.update:{draft_id}"
        existing = await self._idempotent_response(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
        )
        if existing is not None:
            draft = await session.scalar(
                select(RuleSetDraft).where(RuleSetDraft.id == existing)
            )
            if draft is None:
                raise RuntimeError("rule set update idempotency record is invalid")
            return draft
        draft = await session.scalar(
            select(RuleSetDraft)
            .where(
                RuleSetDraft.id == draft_id,
                RuleSetDraft.tenant_id == tenant_id,
                RuleSetDraft.project_id == project_id,
            )
            .with_for_update()
        )
        if draft is None:
            raise LookupError("rule set draft not found")
        if draft.revision != expected_revision:
            raise PersistenceConflictError(
                f"rule set draft revision is {draft.revision}, expected {expected_revision}"
            )
        draft.rules = rules
        draft.revision += 1
        draft.updated_by = actor
        draft.updated_at = datetime.now(UTC)
        await session.flush()
        await self._record_idempotency(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
            response_ref=draft.id,
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="rule-set.update",
            resource_type="rule_set",
            resource_id=str(draft.rule_set_id),
            metadata={"revision": draft.revision},
        )
        return cast(RuleSetDraft, draft)

    def validate(
        self,
        rules: dict[str, Any],
        *,
        attachments: list[dict[str, Any]] | None = None,
    ) -> tuple[IntegrityRuleDocument, IntegrityResult | None]:
        document = IntegrityRuleDocument.model_validate(rules)
        preview = None
        if attachments is not None:
            preview = evaluate_integrity(
                rule_set_version_id="draft-preview",
                document=document,
                attachments=[AttachmentInput.model_validate(item) for item in attachments],
                attachment_manifest_hash=canonical_hash(attachments),
            )
        return document, preview

    async def publish(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        draft_id: UUID,
        idempotency_key: str,
        actor: str,
    ) -> RuleSetVersion:
        draft = await session.scalar(
            select(RuleSetDraft).where(
                RuleSetDraft.id == draft_id,
                RuleSetDraft.tenant_id == tenant_id,
                RuleSetDraft.project_id == project_id,
            )
        )
        if draft is None:
            raise LookupError("rule set draft not found")
        document = IntegrityRuleDocument.model_validate(draft.rules)
        digest = canonical_hash(document.model_dump(mode="json", by_alias=True))
        request_hash = canonical_hash({"draftId": str(draft_id), "contentHash": digest})
        operation = f"rule-set.publish:{draft_id}"
        idempotent = await self._idempotent_response(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
        )
        if idempotent is not None:
            version = await session.get(RuleSetVersion, idempotent)
            if version is None:
                raise RuntimeError("rule set publish idempotency record is invalid")
            return version
        existing = await session.scalar(
            select(RuleSetVersion).where(
                RuleSetVersion.rule_set_id == draft.rule_set_id,
                RuleSetVersion.content_hash == digest,
            )
        )
        if existing is not None:
            await self._record_idempotency(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                operation=operation,
                key=idempotency_key,
                request_hash=request_hash,
                response_ref=existing.id,
            )
            return existing
        latest = await session.scalar(
            select(func.max(RuleSetVersion.version)).where(
                RuleSetVersion.rule_set_id == draft.rule_set_id
            )
        )
        version = RuleSetVersion(
            tenant_id=tenant_id,
            project_id=project_id,
            rule_set_id=draft.rule_set_id,
            version=(latest or 0) + 1,
            schema_version=document.schema_version,
            match_expression=document.match,
            rules=document.model_dump(mode="json", by_alias=True),
            content_hash=digest,
            status="PUBLISHED",
            created_by=actor,
        )
        session.add(version)
        await session.flush()
        await self._record_idempotency(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            operation=operation,
            key=idempotency_key,
            request_hash=request_hash,
            response_ref=version.id,
        )
        await _outbox(
            session,
            tenant_id=tenant_id,
            aggregate_id=draft.rule_set_id,
            source_id=version.id,
            event_type="capability.rule-set.published",
            payload={
                "ruleSetId": str(draft.rule_set_id),
                "ruleSetVersionId": str(version.id),
                "contentHash": digest,
            },
        )
        await self._audit.append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="rule-set.publish",
            resource_type="rule_set_version",
            resource_id=str(version.id),
            metadata={"contentHash": digest},
        )
        return version

    async def select_version(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        payload: dict[str, Any],
    ) -> RuleSetVersion:
        versions = list(
            await session.scalars(
                select(RuleSetVersion).where(
                    RuleSetVersion.tenant_id == tenant_id,
                    RuleSetVersion.project_id == project_id,
                    RuleSetVersion.status == "PUBLISHED",
                )
            )
        )
        selected_id, _ = select_unique_rule(
            payload,
            [(str(version.id), version.match_expression) for version in versions],
        )
        return next(version for version in versions if str(version.id) == selected_id)

    @staticmethod
    async def _idempotent_response(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        operation: str,
        key: str,
        request_hash: str,
    ) -> UUID | None:
        record = await session.get(IdempotencyKey, (tenant_id, project_id, operation, key))
        if record is None:
            return None
        if record.request_hash != request_hash:
            raise ValueError("IDEMPOTENCY_KEY_REUSED")
        return record.response_ref

    @staticmethod
    async def _record_idempotency(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        operation: str,
        key: str,
        request_hash: str,
        response_ref: UUID,
    ) -> None:
        session.add(
            IdempotencyKey(
                tenant_id=tenant_id,
                project_id=project_id,
                operation=operation,
                key=key,
                request_hash=request_hash,
                response_ref=response_ref,
                expires_at=datetime.now(UTC) + timedelta(hours=24),
            )
        )
        await session.flush()


async def _outbox(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    aggregate_id: UUID,
    source_id: UUID,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    session.add(
        OutboxEvent(
            id=uuid7(),
            tenant_id=tenant_id,
            aggregate_id=aggregate_id,
            destination="nats",
            partition_key=str(aggregate_id),
            source_id=source_id,
            type=event_type,
            payload=payload,
        )
    )
