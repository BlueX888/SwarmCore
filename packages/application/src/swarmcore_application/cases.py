from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_domain import SubjectRole
from swarmcore_persistence.models import (
    BusinessObject,
    BusinessObjectVersion,
    CapabilityResourceBinding,
    Evaluation,
    ProjectCapabilityDecisionBinding,
    WorkItem,
    WorkItemRevision,
    WorkItemSubject,
)

from .capability_packs import CapabilityPackService
from .decision_assets import DecisionExecutionService
from .workbench import WorkbenchService


@dataclass(frozen=True, slots=True)
class CaseSubjectInput:
    business_object_id: UUID
    business_object_version_id: UUID
    role: str
    subject_key: str


class CaseService:
    def __init__(
        self, workbench: WorkbenchService, capability_packs: CapabilityPackService
    ) -> None:
        self._workbench = workbench
        self._capability_packs = capability_packs
        self._decisions = DecisionExecutionService()

    async def create(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        scenario_type: str,
        business_work_key: str | None = None,
        payload: dict[str, Any],
        subjects: list[CaseSubjectInput],
        owner: str | None,
        idempotency_key: str,
        actor: str,
    ) -> tuple[WorkItem, WorkItemRevision, list[WorkItemSubject]]:
        _, manifest, _ = await self._capability_packs.resolve_enabled(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            work_item_type=scenario_type,
        )
        await self._validate_subjects(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            manifest=manifest,
            subjects=subjects,
        )
        enriched_payload = _enrich_case_payload(scenario_type, payload, subjects)
        item, revision = await self._workbench.create_work_item(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            work_item_type=scenario_type,
            business_work_key=business_work_key,
            payload=enriched_payload,
            owner=owner,
            idempotency_key=idempotency_key,
            actor=actor,
        )
        existing = list(
            await session.scalars(
                select(WorkItemSubject).where(WorkItemSubject.work_item_revision_id == revision.id)
            )
        )
        if existing:
            return item, revision, existing
        values = [
            WorkItemSubject(
                tenant_id=tenant_id,
                project_id=project_id,
                work_item_id=item.id,
                work_item_revision_id=revision.id,
                business_object_id=value.business_object_id,
                business_object_version_id=value.business_object_version_id,
                role=value.role,
                subject_key=value.subject_key,
            )
            for value in subjects
        ]
        session.add_all(values)
        await session.flush()
        return item, revision, values

    async def list_cases(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[WorkItem], int]:
        return await self._workbench.list_work_items(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            limit=limit,
            offset=offset,
        )

    async def revise(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        payload: dict[str, Any],
        subjects: list[CaseSubjectInput] | None,
        owner: str | None,
        expected_revision: int,
        idempotency_key: str,
        actor: str,
    ) -> tuple[WorkItem, WorkItemRevision, list[WorkItemSubject]]:
        item, _, current_subjects = await self.get(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            case_id=case_id,
        )
        replacements = subjects
        if replacements is not None:
            _, manifest, _ = await self._capability_packs.resolve_enabled(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                work_item_type=item.work_item_type,
            )
            await self._validate_subjects(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                manifest=manifest,
                subjects=replacements,
            )
        fingerprint = None
        if replacements is not None:
            fingerprint = [
                {
                    "businessObjectId": str(value.business_object_id),
                    "businessObjectVersionId": str(value.business_object_version_id),
                    "role": value.role,
                    "subjectKey": value.subject_key,
                }
                for value in replacements
            ]
        subject_source = replacements if replacements is not None else [
            CaseSubjectInput(
                business_object_id=value.business_object_id,
                business_object_version_id=value.business_object_version_id,
                role=value.role,
                subject_key=value.subject_key,
            )
            for value in current_subjects
        ]
        enriched_payload = _enrich_case_payload(item.work_item_type, payload, subject_source)
        item, revision = await self._workbench.update_work_item(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            work_item_id=case_id,
            payload=enriched_payload,
            owner=owner,
            expected_revision=expected_revision,
            idempotency_key=idempotency_key,
            actor=actor,
            copy_subjects=replacements is None,
            subject_fingerprint=fingerprint,
        )
        existing = list(
            await session.scalars(
                select(WorkItemSubject).where(WorkItemSubject.work_item_revision_id == revision.id)
            )
        )
        if existing or replacements is None:
            return item, revision, existing
        values = [
            WorkItemSubject(
                tenant_id=tenant_id,
                project_id=project_id,
                work_item_id=item.id,
                work_item_revision_id=revision.id,
                business_object_id=value.business_object_id,
                business_object_version_id=value.business_object_version_id,
                role=value.role,
                subject_key=value.subject_key,
            )
            for value in replacements
        ]
        session.add_all(values)
        await session.flush()
        return item, revision, values

    async def get(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
    ) -> tuple[WorkItem, WorkItemRevision, list[WorkItemSubject]]:
        item, revision = await self._workbench.get_work_item(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            work_item_id=case_id,
        )
        subjects = list(
            await session.scalars(
                select(WorkItemSubject).where(WorkItemSubject.work_item_revision_id == revision.id)
            )
        )
        return item, revision, subjects

    async def assess(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        idempotency_key: str,
        actor: str,
        submitted_scopes: tuple[str, ...] = (),
        auth_context_hash: str = "unknown",
    ) -> Evaluation:
        item, revision, subjects = await self.get(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            case_id=case_id,
        )
        _, manifest, pack_binding = await self._capability_packs.resolve_enabled(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            work_item_type=item.work_item_type,
        )
        if manifest.spec.case is not None and manifest.spec.case.subjects_required and not subjects:
            raise ValueError("CASE_SUBJECT_REQUIRED")
        decision_bindings = list(
            await session.scalars(
                select(ProjectCapabilityDecisionBinding).where(
                    ProjectCapabilityDecisionBinding.project_capability_binding_id
                    == pack_binding.id
                )
            )
        )
        resource_bindings = list(
            await session.scalars(
                select(CapabilityResourceBinding).where(
                    CapabilityResourceBinding.project_capability_binding_id == pack_binding.id
                )
            )
        )
        decision_slots = {value.slot for value in decision_bindings}
        resource_slots = {value.slot for value in resource_bindings}
        blockers = [
            "DECISION_BINDING_MISSING"
            for slot in manifest.spec.decisions
            if slot.required and slot.slot not in decision_slots
        ]
        blockers.extend(
            "RESOURCE_BINDING_MISSING"
            for slot in manifest.spec.resources
            if slot.required and slot.slot not in resource_slots
        )
        if blockers:
            raise ValueError(",".join(sorted(set(blockers))))
        evaluation = await self._workbench.execute(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            work_item_id=item.id,
            idempotency_key=idempotency_key,
            actor=actor,
            submitted_scopes=submitted_scopes,
            auth_context_hash=auth_context_hash,
        )
        for binding in decision_bindings:
            await self._decisions.freeze(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                evaluation_id=evaluation.id,
                binding=binding,
            )
        del revision
        return evaluation

    @staticmethod
    async def _validate_subjects(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        manifest: Any,
        subjects: list[CaseSubjectInput],
    ) -> None:
        case_contract = manifest.spec.case
        if case_contract is None:
            if subjects:
                raise ValueError("CASE_SUBJECT_SCHEMA_MISMATCH")
            return
        if case_contract.subjects_required and not subjects:
            raise ValueError("CASE_SUBJECT_REQUIRED")
        if subjects and not any(item.role == SubjectRole.PRIMARY.value for item in subjects):
            raise ValueError("CASE_SUBJECT_REQUIRED")
        ids = {item.business_object_id for item in subjects}
        version_ids = {item.business_object_version_id for item in subjects}
        objects = {
            item.id: item
            for item in await session.scalars(
                select(BusinessObject).where(
                    BusinessObject.tenant_id == tenant_id,
                    BusinessObject.project_id == project_id,
                    BusinessObject.id.in_(ids),
                )
            )
        }
        versions = {
            item.id: item
            for item in await session.scalars(
                select(BusinessObjectVersion).where(
                    BusinessObjectVersion.tenant_id == tenant_id,
                    BusinessObjectVersion.project_id == project_id,
                    BusinessObjectVersion.id.in_(version_ids),
                )
            )
        }
        contracts = {item.key: item for item in case_contract.subject_roles}
        counts: dict[str, int] = {}
        for subject in subjects:
            try:
                SubjectRole(subject.role)
            except ValueError as exc:
                raise ValueError("CASE_SUBJECT_SCHEMA_MISMATCH") from exc
            obj = objects.get(subject.business_object_id)
            version = versions.get(subject.business_object_version_id)
            contract = contracts.get(subject.subject_key)
            if (
                obj is None
                or version is None
                or version.business_object_id != obj.id
                or contract is None
                or contract.object_type != obj.object_type
                or contract.role != subject.role
            ):
                raise ValueError("CASE_SUBJECT_SCHEMA_MISMATCH")
            counts[subject.subject_key] = counts.get(subject.subject_key, 0) + 1
        for key, contract in contracts.items():
            count = counts.get(key, 0)
            if count < contract.min or (contract.max is not None and count > contract.max):
                raise ValueError("CASE_SUBJECT_REQUIRED")


def _enrich_case_payload(
    scenario_type: str,
    payload: dict[str, Any],
    subjects: list[CaseSubjectInput],
) -> dict[str, Any]:
    """Fill schema-required identifiers that the workbench derives from subjects."""
    if scenario_type == "invoice-assurance-case":
        return {
            **payload,
            "fieldConfirmations": list(payload.get("fieldConfirmations") or []),
            "humanVerification": dict(payload.get("humanVerification") or {}),
            "enterprisePublicStatusEvidence": dict(
                payload.get("enterprisePublicStatusEvidence") or {}
            ),
        }
    if scenario_type != "contract-performance-case":
        return payload
    existing = payload.get("contractObjectId")
    if isinstance(existing, str) and existing.strip():
        return payload
    primary = next(
        (item for item in subjects if item.subject_key == "contract"),
        None,
    ) or next(
        (item for item in subjects if item.role == "PRIMARY"),
        None,
    ) or (subjects[0] if subjects else None)
    if primary is None:
        return payload
    return {**payload, "contractObjectId": str(primary.business_object_id)}
