from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_domain import uuid7
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.models import (
    BusinessObject,
    BusinessObjectRelation,
    BusinessObjectVersion,
    OutboxEvent,
)
from swarmcore_persistence.repositories import canonical_hash

_OBJECT_TYPE = re.compile(r"^[a-z][a-z0-9-]{0,127}$")
_SCHEMA_REF = re.compile(r"^schema://[^\s@]+@[^\s@]+$")
_MAX_INLINE_BYTES = 256 * 1024
_EVIDENCE_KINDS = {"BLOB", "ARTIFACT", "RESOURCE_SNAPSHOT"}


class BusinessContextError(ValueError):
    pass


class BusinessObjectService:
    def __init__(self) -> None:
        self._audit = AuditRepository()

    async def upsert(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        object_type: str,
        canonical_key: str,
        schema_ref: str,
        data: dict[str, Any],
        provenance: dict[str, Any],
        actor: str,
        effective_at: datetime | None = None,
    ) -> tuple[BusinessObject, BusinessObjectVersion, bool]:
        self._validate_payload(object_type, canonical_key, schema_ref, data)
        business_object = await session.scalar(
            select(BusinessObject)
            .where(
                BusinessObject.tenant_id == tenant_id,
                BusinessObject.project_id == project_id,
                BusinessObject.object_type == object_type,
                BusinessObject.canonical_key == canonical_key,
            )
            .with_for_update()
        )
        created = business_object is None
        if business_object is None:
            business_object = BusinessObject(
                tenant_id=tenant_id,
                project_id=project_id,
                object_type=object_type,
                canonical_key=canonical_key,
                current_version=1,
            )
            session.add(business_object)
            await session.flush()
        version, version_created = await self._add_version(
            session,
            business_object=business_object,
            schema_ref=schema_ref,
            data=data,
            provenance=provenance,
            actor=actor,
            effective_at=effective_at,
            initial=created,
        )
        if created:
            await self._record_change(session, business_object, version, actor, "created")
        elif version_created:
            await self._record_change(session, business_object, version, actor, "versioned")
        return business_object, version, version_created

    async def add_version(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        object_id: UUID,
        schema_ref: str,
        data: dict[str, Any],
        provenance: dict[str, Any],
        actor: str,
        effective_at: datetime | None = None,
    ) -> tuple[BusinessObjectVersion, bool]:
        business_object = await session.scalar(
            select(BusinessObject)
            .where(
                BusinessObject.id == object_id,
                BusinessObject.tenant_id == tenant_id,
                BusinessObject.project_id == project_id,
            )
            .with_for_update()
        )
        if business_object is None:
            raise LookupError("BUSINESS_OBJECT_NOT_FOUND")
        self._validate_payload(
            business_object.object_type, business_object.canonical_key, schema_ref, data
        )
        version, created = await self._add_version(
            session,
            business_object=business_object,
            schema_ref=schema_ref,
            data=data,
            provenance=provenance,
            actor=actor,
            effective_at=effective_at,
            initial=False,
        )
        if created:
            await self._record_change(session, business_object, version, actor, "versioned")
        return version, created

    async def list_objects(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        object_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[BusinessObject]:
        query = select(BusinessObject).where(
            BusinessObject.tenant_id == tenant_id, BusinessObject.project_id == project_id
        )
        if object_type is not None:
            query = query.where(BusinessObject.object_type == object_type)
        return list(
            await session.scalars(
                query.order_by(BusinessObject.updated_at.desc(), BusinessObject.id)
                .offset(offset)
                .limit(min(max(limit, 1), 200))
            )
        )

    async def get(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        object_id: UUID,
    ) -> tuple[BusinessObject, BusinessObjectVersion]:
        business_object = await session.scalar(
            select(BusinessObject).where(
                BusinessObject.id == object_id,
                BusinessObject.tenant_id == tenant_id,
                BusinessObject.project_id == project_id,
            )
        )
        if business_object is None:
            raise LookupError("BUSINESS_OBJECT_NOT_FOUND")
        version = await session.scalar(
            select(BusinessObjectVersion).where(
                BusinessObjectVersion.business_object_id == object_id,
                BusinessObjectVersion.version == business_object.current_version,
            )
        )
        if version is None:
            raise RuntimeError("business object current version is missing")
        return business_object, version

    async def assert_relation(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        source_object_id: UUID,
        source_version_id: UUID,
        target_object_id: UUID,
        target_version_id: UUID,
        relation_type: str,
        evidence: list[dict[str, Any]],
        actor: str,
        assertion_state: str = "ACTIVE",
        supersedes_relation_id: UUID | None = None,
    ) -> BusinessObjectRelation:
        for item in evidence:
            validate_evidence_ref(item)
        objects = list(
            await session.scalars(
                select(BusinessObject).where(
                    BusinessObject.tenant_id == tenant_id,
                    BusinessObject.project_id == project_id,
                    BusinessObject.id.in_((source_object_id, target_object_id)),
                )
            )
        )
        if {item.id for item in objects} != {source_object_id, target_object_id}:
            raise BusinessContextError("OBJECT_RELATION_SCOPE_MISMATCH")
        versions = list(
            await session.scalars(
                select(BusinessObjectVersion).where(
                    BusinessObjectVersion.tenant_id == tenant_id,
                    BusinessObjectVersion.project_id == project_id,
                    BusinessObjectVersion.id.in_((source_version_id, target_version_id)),
                )
            )
        )
        owners = {item.id: item.business_object_id for item in versions}
        if (
            owners.get(source_version_id) != source_object_id
            or owners.get(target_version_id) != target_object_id
        ):
            raise BusinessContextError("OBJECT_RELATION_SCOPE_MISMATCH")
        content = {
            "sourceObjectId": str(source_object_id),
            "sourceVersionId": str(source_version_id),
            "targetObjectId": str(target_object_id),
            "targetVersionId": str(target_version_id),
            "relationType": relation_type,
            "assertionState": assertion_state,
            "evidence": evidence,
            "supersedesRelationId": str(supersedes_relation_id) if supersedes_relation_id else None,
        }
        digest = canonical_hash(content)
        existing = await session.scalar(
            select(BusinessObjectRelation).where(
                BusinessObjectRelation.project_id == project_id,
                BusinessObjectRelation.content_hash == digest,
            )
        )
        if existing is not None:
            return existing
        relation = BusinessObjectRelation(
            tenant_id=tenant_id,
            project_id=project_id,
            source_object_id=source_object_id,
            source_version_id=source_version_id,
            target_object_id=target_object_id,
            target_version_id=target_version_id,
            relation_type=relation_type,
            assertion_state=assertion_state,
            evidence=evidence,
            supersedes_relation_id=supersedes_relation_id,
            content_hash=digest,
            created_by=actor,
        )
        session.add(relation)
        await session.flush()
        await _outbox(
            session,
            tenant_id,
            source_object_id,
            relation.id,
            "business.object.relation_asserted",
            {"relationId": str(relation.id), "contentHash": digest},
        )
        return relation

    async def list_relations(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        object_id: UUID,
    ) -> list[BusinessObjectRelation]:
        return list(
            await session.scalars(
                select(BusinessObjectRelation)
                .where(
                    BusinessObjectRelation.tenant_id == tenant_id,
                    BusinessObjectRelation.project_id == project_id,
                    or_(
                        BusinessObjectRelation.source_object_id == object_id,
                        BusinessObjectRelation.target_object_id == object_id,
                    ),
                )
                .order_by(BusinessObjectRelation.created_at, BusinessObjectRelation.id)
            )
        )

    async def _add_version(
        self,
        session: AsyncSession,
        *,
        business_object: BusinessObject,
        schema_ref: str,
        data: dict[str, Any],
        provenance: dict[str, Any],
        actor: str,
        effective_at: datetime | None,
        initial: bool,
    ) -> tuple[BusinessObjectVersion, bool]:
        digest = canonical_hash(data)
        existing = await session.scalar(
            select(BusinessObjectVersion).where(
                BusinessObjectVersion.business_object_id == business_object.id,
                BusinessObjectVersion.data_hash == digest,
            )
        )
        if existing is not None:
            return existing, False
        number = 1 if initial else business_object.current_version + 1
        version = BusinessObjectVersion(
            tenant_id=business_object.tenant_id,
            project_id=business_object.project_id,
            business_object_id=business_object.id,
            version=number,
            schema_ref=schema_ref,
            data=data,
            data_hash=digest,
            provenance=provenance,
            effective_at=effective_at,
            recorded_by=actor,
        )
        session.add(version)
        business_object.current_version = number
        await session.flush()
        return version, True

    async def _record_change(
        self,
        session: AsyncSession,
        business_object: BusinessObject,
        version: BusinessObjectVersion,
        actor: str,
        change: str,
    ) -> None:
        await self._audit.append(
            session,
            tenant_id=business_object.tenant_id,
            project_id=business_object.project_id,
            actor_id=actor,
            action=f"business-object.{change}",
            resource_type="business_object",
            resource_id=str(business_object.id),
            metadata={"version": version.version, "dataHash": version.data_hash},
        )
        await _outbox(
            session,
            business_object.tenant_id,
            business_object.id,
            version.id,
            f"business.object.{change}",
            {
                "businessObjectId": str(business_object.id),
                "versionId": str(version.id),
                "version": version.version,
                "dataHash": version.data_hash,
            },
        )

    @staticmethod
    def _validate_payload(
        object_type: str, canonical_key: str, schema_ref: str, data: dict[str, Any]
    ) -> None:
        if not _OBJECT_TYPE.fullmatch(object_type) or not canonical_key.strip():
            raise BusinessContextError("BUSINESS_OBJECT_KEY_CONFLICT")
        if not _SCHEMA_REF.fullmatch(schema_ref):
            raise BusinessContextError("BUSINESS_OBJECT_SCHEMA_INVALID")
        if (
            len(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode())
            > _MAX_INLINE_BYTES
        ):
            raise BusinessContextError("BUSINESS_OBJECT_INLINE_LIMIT_EXCEEDED")


def validate_evidence_ref(value: dict[str, Any]) -> None:
    source = value.get("source")
    if not isinstance(source, dict) or source.get("kind") not in _EVIDENCE_KINDS:
        raise BusinessContextError("EVIDENCE_REF_INVALID")
    ref = source.get("ref")
    content_hash = source.get("contentHash")
    if not isinstance(ref, str) or "://" not in ref:
        raise BusinessContextError("EVIDENCE_REF_INVALID")
    if not isinstance(content_hash, str) or len(content_hash) != 64:
        raise BusinessContextError("EVIDENCE_REF_INVALID")
    locator = value.get("locator", {})
    if not isinstance(locator, dict):
        raise BusinessContextError("EVIDENCE_REF_INVALID")


async def _outbox(
    session: AsyncSession,
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
