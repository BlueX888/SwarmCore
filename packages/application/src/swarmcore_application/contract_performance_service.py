from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_domain import uuid7
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.models import (
    ContractPerformanceCase,
    ContractPerformanceCollectionCursor,
    ContractPerformanceEvidence,
    ContractPerformanceEvidenceLink,
    ContractPerformancePlanVersion,
    ContractPerformanceSnapshot,
    OutboxEvent,
)
from swarmcore_persistence.repositories import canonical_hash

from .contract_performance import (
    apply_approved_changes,
    build_daily_reminders,
    build_schedule,
    calculate_status,
    finalize_contract_performance,
    match_evidence,
    normalize_plan,
)


class ContractPerformanceService:
    async def create_case(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        contract_object_id: UUID,
        timezone: str,
        currency: str,
        idempotency_key: str,
        actor: str,
    ) -> ContractPerformanceCase:
        request_hash = canonical_hash(
            {
                "contractObjectId": str(contract_object_id),
                "timezone": timezone,
                "currency": currency,
            }
        )
        existing = await session.scalar(
            select(ContractPerformanceCase).where(
                ContractPerformanceCase.tenant_id == tenant_id,
                ContractPerformanceCase.project_id == project_id,
                ContractPerformanceCase.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            if existing.request_hash != request_hash:
                raise ValueError("IDEMPOTENCY_KEY_REUSED")
            return existing
        value = ContractPerformanceCase(
            tenant_id=tenant_id,
            project_id=project_id,
            contract_object_id=contract_object_id,
            timezone=timezone,
            currency=currency,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            created_by=actor,
        )
        session.add(value)
        await session.flush()
        await AuditRepository().append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="contract-performance.case.create",
            resource_type="contract_performance_case",
            resource_id=str(value.id),
            metadata={"requestHash": request_hash},
        )
        return value

    async def initialize(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        candidates: Mapping[str, Any],
        as_of: date,
        coverage: Mapping[str, Any],
        actor: str,
    ) -> ContractPerformancePlanVersion:
        case = await self._case(session, tenant_id, project_id, case_id)
        plan = normalize_plan(
            candidates,
            timezone=case.timezone,
            currency=case.currency,
        )
        changes = apply_approved_changes(
            plan,
            [item for item in plan.get("changes") or [] if isinstance(item, Mapping)],
            as_of=as_of,
        )
        plan_hash = str(changes["currentBaseline"]["planHash"])
        existing = await session.scalar(
            select(ContractPerformancePlanVersion).where(
                ContractPerformancePlanVersion.tenant_id == tenant_id,
                ContractPerformancePlanVersion.project_id == project_id,
                ContractPerformancePlanVersion.case_id == case_id,
                ContractPerformancePlanVersion.plan_hash == plan_hash,
            )
        )
        if existing is not None:
            return existing
        version = (
            await session.scalar(
                select(func.max(ContractPerformancePlanVersion.version)).where(
                    ContractPerformancePlanVersion.tenant_id == tenant_id,
                    ContractPerformancePlanVersion.project_id == project_id,
                    ContractPerformancePlanVersion.case_id == case_id,
                )
            )
            or 0
        ) + 1
        value = ContractPerformancePlanVersion(
            tenant_id=tenant_id,
            project_id=project_id,
            case_id=case_id,
            version=version,
            status=str(plan["status"]),
            original_baseline=changes["originalBaseline"],
            current_baseline=changes["currentBaseline"],
            coverage=dict(coverage),
            change_history={
                "appliedChanges": changes["appliedChanges"],
                "unapprovedChangeRisks": changes["unapprovedChangeRisks"],
                "differences": changes["differences"],
            },
            plan_hash=plan_hash,
        )
        session.add(value)
        case.status = "PLAN_REVIEW"
        await session.flush()
        await AuditRepository().append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="contract-performance.plan.initialize",
            resource_type="contract_performance_plan",
            resource_id=str(value.id),
            metadata={"planHash": plan_hash, "version": version},
        )
        return value

    async def publish_plan(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        version: int,
        approval_id: UUID,
        actor: str,
        confirmations: Sequence[Mapping[str, Any]] = (),
    ) -> ContractPerformancePlanVersion:
        case = await self._case(session, tenant_id, project_id, case_id)
        plan_version = await self._plan_by_number(session, tenant_id, project_id, case_id, version)
        if plan_version.status == "PUBLISHED":
            if plan_version.approval_id != approval_id:
                raise ValueError("plan version already published with another approval")
            return plan_version
        confirmed_codes = {
            str(item.get("code")) for item in confirmations if item.get("confirmed") is True
        }
        unresolved = [
            item
            for item in (
                list(plan_version.current_baseline.get("conflicts") or [])
                + list(plan_version.current_baseline.get("gaps") or [])
            )
            if str(item.get("code")) not in confirmed_codes
        ]
        if unresolved:
            raise ValueError("PLAN_REVIEW_ITEMS_UNRESOLVED")
        previous = (
            await session.scalars(
                select(ContractPerformancePlanVersion).where(
                    ContractPerformancePlanVersion.tenant_id == tenant_id,
                    ContractPerformancePlanVersion.project_id == project_id,
                    ContractPerformancePlanVersion.case_id == case_id,
                    ContractPerformancePlanVersion.status == "PUBLISHED",
                )
            )
        ).all()
        for item in previous:
            item.status = "SUPERSEDED"
        plan_version.status = "PUBLISHED"
        plan_version.current_baseline = {
            **plan_version.current_baseline,
            "status": "PUBLISHED",
        }
        published_hash = canonical_hash(
            {
                key: value
                for key, value in plan_version.current_baseline.items()
                if key != "planHash"
            }
        )
        plan_version.current_baseline = {
            **plan_version.current_baseline,
            "planHash": published_hash,
        }
        plan_version.plan_hash = published_hash
        plan_version.published_by = actor
        plan_version.approval_id = approval_id
        plan_version.effective_at = datetime.now(UTC)
        plan_version.review_decisions = [
            *plan_version.review_decisions,
            {
                "approvalId": str(approval_id),
                "actor": actor,
                "decidedAt": plan_version.effective_at.isoformat(),
                "action": "PUBLISH",
                "confirmations": [dict(item) for item in confirmations],
            },
        ]
        case.active_plan_version_id = plan_version.id
        case.status = "ACTIVE"
        self._outbox(
            session,
            tenant_id=tenant_id,
            aggregate_id=case.id,
            source_id=plan_version.id,
            event_type="contract.performance.plan.published.v1",
            payload={
                "tenantId": str(tenant_id),
                "projectId": str(project_id),
                "caseId": str(case.id),
                "planVersion": plan_version.version,
                "planHash": plan_version.plan_hash,
            },
        )
        await AuditRepository().append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="contract-performance.plan.publish",
            resource_type="contract_performance_plan",
            resource_id=str(plan_version.id),
            metadata={
                "approvalId": str(approval_id),
                "planHash": plan_version.plan_hash,
                "version": plan_version.version,
            },
        )
        await session.flush()
        return plan_version

    async def collect(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        as_of: date,
        evidence: Sequence[Mapping[str, Any]],
        candidate_links: Sequence[Mapping[str, Any]],
        sources: Sequence[Mapping[str, Any]],
        collection_status: str,
        idempotency_key: str,
        actor: str,
        approved_exceptions: Sequence[str] = (),
    ) -> ContractPerformanceSnapshot:
        case = await self._case(session, tenant_id, project_id, case_id)
        if case.active_plan_version_id is None:
            raise ValueError("PUBLISHED_PLAN_REQUIRED")
        plan_version = await session.scalar(
            select(ContractPerformancePlanVersion).where(
                ContractPerformancePlanVersion.tenant_id == tenant_id,
                ContractPerformancePlanVersion.project_id == project_id,
                ContractPerformancePlanVersion.case_id == case_id,
                ContractPerformancePlanVersion.id == case.active_plan_version_id,
            )
        )
        if plan_version is None or plan_version.status != "PUBLISHED":
            raise ValueError("PUBLISHED_PLAN_REQUIRED")
        request_hash = canonical_hash(
            {
                "caseId": str(case_id),
                "planVersionId": str(plan_version.id),
                "asOf": as_of.isoformat(),
                "evidence": [dict(item) for item in evidence],
                "candidateLinks": [dict(item) for item in candidate_links],
                "sources": [dict(item) for item in sources],
                "collectionStatus": collection_status,
                "approvedExceptions": list(approved_exceptions),
            }
        )
        prior = await session.scalar(
            select(ContractPerformanceSnapshot).where(
                ContractPerformanceSnapshot.tenant_id == tenant_id,
                ContractPerformanceSnapshot.project_id == project_id,
                ContractPerformanceSnapshot.case_id == case_id,
                ContractPerformanceSnapshot.idempotency_key == idempotency_key,
            )
        )
        if prior is not None:
            if prior.request_hash != request_hash:
                raise ValueError("IDEMPOTENCY_KEY_REUSED")
            return prior
        previous_snapshot = await session.scalar(
            select(ContractPerformanceSnapshot)
            .where(
                ContractPerformanceSnapshot.tenant_id == tenant_id,
                ContractPerformanceSnapshot.project_id == project_id,
                ContractPerformanceSnapshot.case_id == case_id,
            )
            .order_by(ContractPerformanceSnapshot.created_at.desc())
            .limit(1)
        )

        persisted, source_ids = await self._persist_evidence(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            case_id=case_id,
            evidence=evidence,
        )
        normalized_candidates = [
            {
                **dict(item),
                "evidenceId": source_ids.get(
                    str(item.get("evidenceId")), str(item.get("evidenceId"))
                ),
            }
            for item in candidate_links
        ]
        match_result = match_evidence(
            plan_version.current_baseline,
            persisted,
            normalized_candidates,
        )
        await self._persist_links(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            case_id=case_id,
            links=match_result["links"],
        )
        await session.flush()
        all_evidence_rows = (
            await session.scalars(
                select(ContractPerformanceEvidence).where(
                    ContractPerformanceEvidence.tenant_id == tenant_id,
                    ContractPerformanceEvidence.project_id == project_id,
                    ContractPerformanceEvidence.case_id == case_id,
                )
            )
        ).all()
        all_evidence = [
            {
                **item.snapshot,
                "id": str(item.id),
                "contentHash": item.content_hash,
            }
            for item in all_evidence_rows
        ]
        all_link_rows = (
            await session.scalars(
                select(ContractPerformanceEvidenceLink).where(
                    ContractPerformanceEvidenceLink.tenant_id == tenant_id,
                    ContractPerformanceEvidenceLink.project_id == project_id,
                    ContractPerformanceEvidenceLink.case_id == case_id,
                )
            )
        ).all()
        all_links = [
            {
                "evidenceId": str(item.evidence_id),
                "targetType": item.target_type,
                "targetId": item.target_id,
                "matchStatus": item.match_status,
                "matchReasons": list(item.match_reasons),
                "confirmedBy": item.confirmed_by,
            }
            for item in all_link_rows
        ]
        performance = calculate_status(
            plan_version.current_baseline,
            all_evidence,
            all_links,
            as_of=as_of,
            collection_status=collection_status,
            approved_exceptions=approved_exceptions,
        )
        actuals = {
            item["milestoneId"]: {
                "status": item["status"],
                "evidenceStatus": ("COMPLETE" if not item["missingEvidenceTypes"] else "PENDING"),
                "actualStartDate": item["actualStartDate"],
                "actualFinishDate": item["actualFinishDate"],
            }
            for item in performance["milestones"]
        }
        gantt = build_schedule(
            plan_version.current_baseline,
            original_plan=plan_version.original_baseline,
            actuals=actuals,
            as_of=as_of,
        )
        result = finalize_contract_performance(
            case_id=str(case.id),
            plan_version=plan_version.version,
            plan=plan_version.current_baseline,
            performance=performance,
            gantt=gantt,
            evidence_ledger={
                "evidence": all_evidence,
                "links": all_links,
                "unmatchedEvidenceIds": [
                    item["evidenceId"]
                    for item in all_links
                    if item["matchStatus"] == "UNMATCHED"
                ],
            },
            change_history=plan_version.change_history,
            provenance={
                "planHash": plan_version.plan_hash,
                "ruleSetRef": "rule://contract-performance@2",
                "toolRefs": [
                    "tool://contract-performance/evidence-match@1",
                    "tool://contract-performance/status-calculate@2",
                    "tool://contract-performance/schedule-build@1",
                    "tool://contract-performance/finalize@1",
                ],
            },
            approvals=[
                {
                    "actor": actor,
                    "decision": "LIMITED_EXCEPTION",
                    "scope": value,
                }
                for value in approved_exceptions
            ],
        )
        snapshot = ContractPerformanceSnapshot(
            tenant_id=tenant_id,
            project_id=project_id,
            case_id=case_id,
            plan_version_id=plan_version.id,
            as_of=datetime.combine(as_of, datetime.min.time(), tzinfo=UTC),
            status=str(result["status"]),
            collection_status=collection_status,
            result=result,
            result_hash=str(result["resultHash"]),
            gantt_hash=str(gantt["ganttHash"]),
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            created_by=actor,
        )
        session.add(snapshot)
        await session.flush()
        await self._advance_cursors(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            case_id=case_id,
            sources=sources,
        )
        case.status = (
            "COMPLETED"
            if result["status"] == "COMPLETED"
            else "REVIEW_REQUIRED"
            if result["status"] == "REVIEW_REQUIRED"
            else "ACTIVE"
        )
        self._outbox(
            session,
            tenant_id=tenant_id,
            aggregate_id=case.id,
            source_id=snapshot.id,
            event_type="contract.performance.snapshot.finalized.v1",
            payload={
                "tenantId": str(tenant_id),
                "projectId": str(project_id),
                "caseId": str(case.id),
                "snapshotId": str(snapshot.id),
                "status": snapshot.status,
                "resultHash": snapshot.result_hash,
            },
        )
        if persisted:
            self._outbox(
                session,
                tenant_id=tenant_id,
                aggregate_id=case.id,
                source_id=uuid7(),
                event_type="contract.performance.evidence.collected.v1",
                payload={
                    "tenantId": str(tenant_id),
                    "projectId": str(project_id),
                    "caseId": str(case.id),
                    "snapshotId": str(snapshot.id),
                    "evidenceIds": [item["id"] for item in persisted],
                },
            )
        if match_result["links"]:
            self._outbox(
                session,
                tenant_id=tenant_id,
                aggregate_id=case.id,
                source_id=uuid7(),
                event_type="contract.performance.evidence.linked.v1",
                payload={
                    "tenantId": str(tenant_id),
                    "projectId": str(project_id),
                    "caseId": str(case.id),
                    "snapshotId": str(snapshot.id),
                    "links": match_result["links"],
                },
            )
        previous_statuses = self._milestone_statuses(
            previous_snapshot.result if previous_snapshot is not None else {}
        )
        for item in performance["milestones"]:
            milestone_id = str(item["milestoneId"])
            current_status = str(item["status"])
            if previous_statuses.get(milestone_id) == current_status:
                continue
            self._outbox(
                session,
                tenant_id=tenant_id,
                aggregate_id=case.id,
                source_id=uuid7(),
                event_type="contract.performance.milestone.status-changed.v1",
                payload={
                    "tenantId": str(tenant_id),
                    "projectId": str(project_id),
                    "caseId": str(case.id),
                    "snapshotId": str(snapshot.id),
                    "milestoneId": milestone_id,
                    "previousStatus": previous_statuses.get(milestone_id),
                    "status": current_status,
                },
            )
        if performance["reviewRequired"]:
            self._outbox(
                session,
                tenant_id=tenant_id,
                aggregate_id=case.id,
                source_id=uuid7(),
                event_type="contract.performance.review.requested.v1",
                payload={
                    "tenantId": str(tenant_id),
                    "projectId": str(project_id),
                    "caseId": str(case.id),
                    "snapshotId": str(snapshot.id),
                    "findingCodes": [
                        item["code"] for item in performance["findings"]
                    ],
                },
            )
        for reminder in build_daily_reminders(
            plan_version.current_baseline,
            performance,
            as_of=as_of,
        ):
            self._outbox(
                session,
                tenant_id=tenant_id,
                aggregate_id=case.id,
                source_id=uuid7(),
                event_type=str(reminder["type"]),
                payload={
                    "tenantId": str(tenant_id),
                    "projectId": str(project_id),
                    "caseId": str(case.id),
                    **reminder,
                },
            )
        await AuditRepository().append(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            actor_id=actor,
            action="contract-performance.snapshot.finalize",
            resource_type="contract_performance_snapshot",
            resource_id=str(snapshot.id),
            metadata={
                "planVersionId": str(plan_version.id),
                "resultHash": snapshot.result_hash,
                "collectionStatus": collection_status,
            },
        )
        await session.flush()
        return snapshot

    async def get_case(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
    ) -> ContractPerformanceCase:
        return await self._case(session, tenant_id, project_id, case_id)

    async def get_plan(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        version: int | None = None,
    ) -> ContractPerformancePlanVersion:
        if version is not None:
            return await self._plan_by_number(session, tenant_id, project_id, case_id, version)
        case = await self._case(session, tenant_id, project_id, case_id)
        if case.active_plan_version_id is not None:
            value = await session.scalar(
                select(ContractPerformancePlanVersion).where(
                    ContractPerformancePlanVersion.tenant_id == tenant_id,
                    ContractPerformancePlanVersion.project_id == project_id,
                    ContractPerformancePlanVersion.case_id == case_id,
                    ContractPerformancePlanVersion.id == case.active_plan_version_id,
                )
            )
        else:
            value = await session.scalar(
                select(ContractPerformancePlanVersion)
                .where(
                    ContractPerformancePlanVersion.tenant_id == tenant_id,
                    ContractPerformancePlanVersion.project_id == project_id,
                    ContractPerformancePlanVersion.case_id == case_id,
                )
                .order_by(ContractPerformancePlanVersion.version.desc())
                .limit(1)
            )
        if value is None:
            raise LookupError("contract performance plan not found")
        return value

    async def get_snapshot(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        snapshot_id: UUID,
    ) -> ContractPerformanceSnapshot:
        value = await session.scalar(
            select(ContractPerformanceSnapshot).where(
                ContractPerformanceSnapshot.tenant_id == tenant_id,
                ContractPerformanceSnapshot.project_id == project_id,
                ContractPerformanceSnapshot.case_id == case_id,
                ContractPerformanceSnapshot.id == snapshot_id,
            )
        )
        if value is None:
            raise LookupError("contract performance snapshot not found")
        return value

    async def get_latest_snapshot(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        as_of: date | None = None,
    ) -> ContractPerformanceSnapshot | None:
        query = select(ContractPerformanceSnapshot).where(
            ContractPerformanceSnapshot.tenant_id == tenant_id,
            ContractPerformanceSnapshot.project_id == project_id,
            ContractPerformanceSnapshot.case_id == case_id,
        )
        if as_of is not None:
            query = query.where(
                ContractPerformanceSnapshot.as_of
                <= datetime.combine(as_of, datetime.max.time(), tzinfo=UTC)
            )
        value: ContractPerformanceSnapshot | None = await session.scalar(
            query.order_by(
                ContractPerformanceSnapshot.as_of.desc(),
                ContractPerformanceSnapshot.created_at.desc(),
            ).limit(1)
        )
        return value

    async def list_evidence(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        evidence_type: str | None = None,
    ) -> list[ContractPerformanceEvidence]:
        query = select(ContractPerformanceEvidence).where(
            ContractPerformanceEvidence.tenant_id == tenant_id,
            ContractPerformanceEvidence.project_id == project_id,
            ContractPerformanceEvidence.case_id == case_id,
        )
        if evidence_type:
            query = query.where(ContractPerformanceEvidence.evidence_type == evidence_type.upper())
        query = query.order_by(ContractPerformanceEvidence.captured_at.desc())
        return list((await session.scalars(query)).all())

    async def _case(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
    ) -> ContractPerformanceCase:
        value = await session.scalar(
            select(ContractPerformanceCase).where(
                ContractPerformanceCase.tenant_id == tenant_id,
                ContractPerformanceCase.project_id == project_id,
                ContractPerformanceCase.id == case_id,
            )
        )
        if value is None:
            raise LookupError("contract performance case not found")
        return value

    async def _plan_by_number(
        self,
        session: AsyncSession,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        version: int,
    ) -> ContractPerformancePlanVersion:
        value = await session.scalar(
            select(ContractPerformancePlanVersion).where(
                ContractPerformancePlanVersion.tenant_id == tenant_id,
                ContractPerformancePlanVersion.project_id == project_id,
                ContractPerformancePlanVersion.case_id == case_id,
                ContractPerformancePlanVersion.version == version,
            )
        )
        if value is None:
            raise LookupError("contract performance plan not found")
        return value

    async def _persist_evidence(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        evidence: Sequence[Mapping[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, str]]:
        persisted: list[dict[str, Any]] = []
        source_ids: dict[str, str] = {}
        for raw in evidence:
            source_ref = str(raw.get("sourceRef") or "manual")
            source_record_id = str(raw.get("sourceRecordId") or raw.get("id") or uuid7())
            content_hash = str(raw.get("contentHash") or canonical_hash(dict(raw)))
            existing = await session.scalar(
                select(ContractPerformanceEvidence).where(
                    ContractPerformanceEvidence.tenant_id == tenant_id,
                    ContractPerformanceEvidence.project_id == project_id,
                    ContractPerformanceEvidence.case_id == case_id,
                    ContractPerformanceEvidence.source_ref == source_ref,
                    ContractPerformanceEvidence.source_record_id == source_record_id,
                    ContractPerformanceEvidence.content_hash == content_hash,
                )
            )
            source_id = str(raw.get("id") or source_record_id)
            if existing is None:
                snapshot = dict(raw)
                value = ContractPerformanceEvidence(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    case_id=case_id,
                    evidence_type=str(raw.get("type") or "PROGRESS").upper(),
                    source_ref=source_ref,
                    source_record_id=source_record_id,
                    content_hash=content_hash,
                    snapshot=snapshot,
                )
                session.add(value)
                await session.flush()
            else:
                value = existing
            item = {**value.snapshot, "id": str(value.id), "contentHash": value.content_hash}
            persisted.append(item)
            source_ids[source_id] = str(value.id)
        return persisted, source_ids

    async def _persist_links(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        links: Sequence[Mapping[str, Any]],
    ) -> None:
        for link in links:
            evidence_id = UUID(str(link["evidenceId"]))
            target_type = str(link.get("targetType") or "UNKNOWN")
            target_id = str(link.get("targetId") or evidence_id)
            existing = await session.scalar(
                select(ContractPerformanceEvidenceLink).where(
                    ContractPerformanceEvidenceLink.tenant_id == tenant_id,
                    ContractPerformanceEvidenceLink.project_id == project_id,
                    ContractPerformanceEvidenceLink.evidence_id == evidence_id,
                    ContractPerformanceEvidenceLink.target_type == target_type,
                    ContractPerformanceEvidenceLink.target_id == target_id,
                )
            )
            if existing is not None:
                continue
            session.add(
                ContractPerformanceEvidenceLink(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    case_id=case_id,
                    evidence_id=evidence_id,
                    target_type=target_type,
                    target_id=target_id,
                    match_status=str(link["matchStatus"]),
                    match_reasons=list(link.get("matchReasons") or []),
                )
            )

    async def _advance_cursors(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        sources: Sequence[Mapping[str, Any]],
    ) -> None:
        now = datetime.now(UTC)
        for source in sources:
            source_ref = str(source.get("sourceRef") or "")
            if not source_ref:
                continue
            value = await session.scalar(
                select(ContractPerformanceCollectionCursor).where(
                    ContractPerformanceCollectionCursor.tenant_id == tenant_id,
                    ContractPerformanceCollectionCursor.project_id == project_id,
                    ContractPerformanceCollectionCursor.case_id == case_id,
                    ContractPerformanceCollectionCursor.source_ref == source_ref,
                )
            )
            if value is None:
                value = ContractPerformanceCollectionCursor(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    case_id=case_id,
                    source_ref=source_ref,
                    status="PENDING",
                )
                session.add(value)
            value.last_attempt_at = now
            source_status = str(source.get("status") or "SUCCEEDED").upper()
            value.status = source_status
            if source_status == "SUCCEEDED":
                value.cursor = (
                    str(source["nextCursor"])
                    if source.get("nextCursor") is not None
                    else value.cursor
                )
                value.last_success_at = now
                value.error = None
            else:
                value.error = dict(source.get("error") or {})

    @staticmethod
    def _milestone_statuses(result: Mapping[str, Any]) -> dict[str, str]:
        performance = result.get("performance")
        if not isinstance(performance, Mapping):
            return {}
        return {
            str(item.get("milestoneId")): str(item.get("status"))
            for item in performance.get("milestones") or []
            if isinstance(item, Mapping)
        }

    @staticmethod
    def _outbox(
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
                tenant_id=tenant_id,
                aggregate_id=aggregate_id,
                destination="nats",
                partition_key=str(aggregate_id),
                source_id=source_id,
                type=event_type,
                payload=payload,
            )
        )


__all__ = ["ContractPerformanceService"]
