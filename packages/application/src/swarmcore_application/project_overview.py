from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_persistence.models import (
    ApprovalRequest,
    BlobObject,
    BusinessDocument,
    BusinessDocumentVersion,
    DocumentWorkBinding,
    Evaluation,
    ExternalInputRequest,
    Run,
    WorkItem,
)

from .business_works import (
    BusinessWorkBlocker,
    BusinessWorkCategory,
    BusinessWorkService,
    BusinessWorkStatus,
    BusinessWorkSummary,
    document_binding_keys,
)
from .queries import ACTIVE_RUN_STATUSES, RunQueryService, RunSummary

WAITING_RUN_STATUSES = ("WAITING_APPROVAL", "WAITING_INPUT", "PAUSED")


@dataclass(frozen=True, slots=True)
class ProjectOverviewCounts:
    pending_approvals: int
    pending_inputs: int
    documents_available: int
    documents_review_required: int
    documents_failed: int
    active_runs: int
    waiting_runs: int


@dataclass(frozen=True, slots=True)
class ProjectOverviewReadiness:
    required_documents: int
    satisfied_documents: int
    documents_ready: bool
    ready_to_start: bool


@dataclass(frozen=True, slots=True)
class ProjectOverviewRun:
    run_id: UUID
    business_work_key: str | None
    business_work_name: str
    status: str
    strategy_version_id: UUID
    event_count: int
    task_count: int
    operator_name: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    failure_reason: str | None
    cancel_reason: str | None


@dataclass(frozen=True, slots=True)
class ProjectOverviewWork:
    work_key: str
    name: str
    short_name: str
    category: BusinessWorkCategory
    status: BusinessWorkStatus
    status_label: str
    qualification_status: str
    qualification_label: str
    blockers: tuple[BusinessWorkBlocker, ...]
    readiness: ProjectOverviewReadiness
    active_run_id: UUID | None
    latest_run: ProjectOverviewRun | None


@dataclass(frozen=True, slots=True)
class ProjectOverviewSnapshot:
    generated_at: datetime
    counts: ProjectOverviewCounts
    business_works: tuple[ProjectOverviewWork, ...]
    recent_runs: tuple[ProjectOverviewRun, ...]


def calculate_document_readiness(
    requirements: tuple[dict[str, Any], ...],
    available_by_category: dict[str, int],
) -> tuple[int, int, bool]:
    required_total = 0
    satisfied_total = 0
    ready = True
    for requirement in requirements:
        if requirement.get("required") is False:
            continue
        category = requirement.get("category") or requirement.get("key")
        if not isinstance(category, str) or not category:
            continue
        raw_minimum = requirement.get("minCount", 1)
        minimum = raw_minimum if isinstance(raw_minimum, int) else 1
        minimum = max(0, minimum)
        available = max(0, available_by_category.get(category, 0))
        required_total += minimum
        satisfied_total += min(available, minimum)
        ready = ready and available >= minimum
    return required_total, satisfied_total, ready


def calculate_run_counts(run_counts: dict[str, int]) -> tuple[int, int]:
    active = sum(run_counts.get(status, 0) for status in ACTIVE_RUN_STATUSES)
    waiting = sum(run_counts.get(status, 0) for status in WAITING_RUN_STATUSES)
    return active, waiting


def calculate_ready_to_start(runtime_status: str, documents_ready: bool) -> bool:
    return runtime_status == "runnable" and documents_ready


def business_work_index_by_item_type(
    works: list[BusinessWorkSummary],
) -> dict[str, BusinessWorkSummary]:
    index: dict[str, BusinessWorkSummary] = {}
    ambiguous: set[str] = set()
    for work in works:
        if work.work_item_type:
            if work.work_item_type in index:
                ambiguous.add(work.work_item_type)
            else:
                index[work.work_item_type] = work
    for work_item_type in ambiguous:
        index.pop(work_item_type, None)
    return index


class ProjectOverviewService:
    def __init__(
        self,
        business_works: BusinessWorkService,
        run_queries: RunQueryService | None = None,
    ) -> None:
        self._business_works = business_works
        self._run_queries = run_queries or RunQueryService()

    async def get(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> ProjectOverviewSnapshot:
        works = await self._business_works.list_works(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
        )
        strategy_ids = tuple(
            dict.fromkeys(
                work.bound_strategy_version_id
                for work in works
                if work.bound_strategy_version_id is not None
            )
        )
        latest_by_strategy = await self._run_queries.latest_summaries_by_strategy(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            strategy_version_ids=strategy_ids,
        )
        recent_page = await self._run_queries.list_summaries(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            limit=5,
            include_active=False,
        )
        active_by_strategy = await self._active_runs_by_strategy(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            strategy_version_ids=strategy_ids,
        )
        document_counts, available_documents = await self._document_projection(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
        )
        run_labels = await self._run_labels(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            run_ids=tuple(item.run_id for item in recent_page.items),
            works=works,
        )

        work_items: list[ProjectOverviewWork] = []
        for work in works:
            categories = self._available_categories_for_work(work, available_documents)
            required, satisfied, documents_ready = calculate_document_readiness(
                work.document_requirements,
                categories,
            )
            latest = (
                latest_by_strategy.get(work.bound_strategy_version_id)
                if work.bound_strategy_version_id is not None
                else None
            )
            work_items.append(
                ProjectOverviewWork(
                    work_key=work.work_key,
                    name=work.name,
                    short_name=work.short_name,
                    category=work.category,
                    status=work.status,
                    status_label=work.status_label,
                    qualification_status=work.qualification_status,
                    qualification_label=work.qualification_label,
                    blockers=work.blockers,
                    readiness=ProjectOverviewReadiness(
                        required_documents=required,
                        satisfied_documents=satisfied,
                        documents_ready=documents_ready,
                        ready_to_start=calculate_ready_to_start(work.status, documents_ready),
                    ),
                    active_run_id=(
                        active_by_strategy.get(work.bound_strategy_version_id)
                        if work.bound_strategy_version_id is not None
                        else None
                    ),
                    latest_run=(
                        self._overview_run(latest, work_key=work.work_key, work_name=work.name)
                        if latest is not None
                        else None
                    ),
                )
            )

        recent_runs = tuple(
            self._overview_run(
                summary,
                work_key=run_labels.get(summary.run_id, (None, "平台运行"))[0],
                work_name=run_labels.get(summary.run_id, (None, "平台运行"))[1],
            )
            for summary in recent_page.items[:5]
        )
        counts = await self._counts(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            document_counts=document_counts,
        )
        return ProjectOverviewSnapshot(
            generated_at=datetime.now(UTC),
            counts=counts,
            business_works=tuple(work_items),
            recent_runs=recent_runs,
        )

    async def _counts(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        document_counts: dict[str, int],
    ) -> ProjectOverviewCounts:
        pending_approvals = await session.scalar(
            select(func.count())
            .select_from(ApprovalRequest)
            .where(
                ApprovalRequest.tenant_id == tenant_id,
                ApprovalRequest.project_id == project_id,
                ApprovalRequest.status == "PENDING",
            )
        )
        pending_inputs = await session.scalar(
            select(func.count())
            .select_from(ExternalInputRequest)
            .where(
                ExternalInputRequest.tenant_id == tenant_id,
                ExternalInputRequest.project_id == project_id,
                ExternalInputRequest.status == "PENDING",
            )
        )
        run_rows = await session.execute(
            select(Run.status, func.count(Run.id))
            .where(Run.tenant_id == tenant_id, Run.project_id == project_id)
            .group_by(Run.status)
        )
        run_counts = {status: int(count) for status, count in run_rows}
        active_runs, waiting_runs = calculate_run_counts(run_counts)
        return ProjectOverviewCounts(
            pending_approvals=int(pending_approvals or 0),
            pending_inputs=int(pending_inputs or 0),
            documents_available=document_counts.get("AVAILABLE", 0),
            documents_review_required=document_counts.get("REVIEW_REQUIRED", 0),
            documents_failed=document_counts.get("FAILED", 0),
            active_runs=active_runs,
            waiting_runs=waiting_runs,
        )

    async def _document_projection(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
    ) -> tuple[dict[str, int], dict[str, dict[str, set[UUID]]]]:
        count_rows = await session.execute(
            select(BusinessDocument.status, func.count(BusinessDocument.id))
            .where(
                BusinessDocument.tenant_id == tenant_id,
                BusinessDocument.project_id == project_id,
            )
            .group_by(BusinessDocument.status)
        )
        counts = {status: int(count) for status, count in count_rows}
        rows = await session.execute(
            select(
                DocumentWorkBinding.business_work_key,
                BusinessDocument.category,
                BusinessDocument.id,
            )
            .join(
                BusinessDocument,
                BusinessDocument.id == DocumentWorkBinding.business_document_id,
            )
            .join(
                BusinessDocumentVersion,
                (BusinessDocumentVersion.business_document_id == BusinessDocument.id)
                & (BusinessDocumentVersion.version == BusinessDocument.current_version),
            )
            .join(BlobObject, BlobObject.id == BusinessDocumentVersion.blob_id)
            .where(
                BusinessDocument.tenant_id == tenant_id,
                BusinessDocument.project_id == project_id,
                DocumentWorkBinding.tenant_id == tenant_id,
                DocumentWorkBinding.project_id == project_id,
                BusinessDocument.status == "AVAILABLE",
                BlobObject.status == "AVAILABLE",
                BlobObject.scan_status == "CLEAN",
                BlobObject.retention_until > datetime.now(UTC),
            )
        )
        available: dict[str, dict[str, set[UUID]]] = {}
        for binding_key, category, document_id in rows:
            available.setdefault(binding_key, {}).setdefault(category, set()).add(document_id)
        return counts, available

    @staticmethod
    def _available_categories_for_work(
        work: BusinessWorkSummary,
        available_documents: dict[str, dict[str, set[UUID]]],
    ) -> dict[str, int]:
        keys = {work.work_key}
        if work.pack_name and work.work_item_type:
            keys.update(document_binding_keys(work.pack_name, work.work_item_type))
        elif work.pack_name:
            keys.add(work.pack_name)
        by_category: dict[str, set[UUID]] = {}
        for key in keys:
            for category, document_ids in available_documents.get(key, {}).items():
                by_category.setdefault(category, set()).update(document_ids)
        return {category: len(document_ids) for category, document_ids in by_category.items()}

    @staticmethod
    async def _active_runs_by_strategy(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        strategy_version_ids: tuple[UUID, ...],
    ) -> dict[UUID, UUID]:
        if not strategy_version_ids:
            return {}
        rows = await session.execute(
            select(Run.strategy_version_id, Run.id)
            .where(
                Run.tenant_id == tenant_id,
                Run.project_id == project_id,
                Run.strategy_version_id.in_(strategy_version_ids),
                Run.status.in_(ACTIVE_RUN_STATUSES),
            )
            .order_by(Run.created_at.desc())
        )
        result: dict[UUID, UUID] = {}
        for strategy_version_id, run_id in rows:
            result.setdefault(strategy_version_id, run_id)
        return result

    @staticmethod
    async def _run_labels(
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        run_ids: tuple[UUID, ...],
        works: list[BusinessWorkSummary],
    ) -> dict[UUID, tuple[str | None, str]]:
        if not run_ids:
            return {}
        by_work_item_type = business_work_index_by_item_type(works)
        rows = await session.execute(
            select(Evaluation.run_id, WorkItem.business_work_key, WorkItem.work_item_type)
            .join(WorkItem, WorkItem.id == Evaluation.work_item_id)
            .where(
                Evaluation.tenant_id == tenant_id,
                Evaluation.project_id == project_id,
                WorkItem.tenant_id == tenant_id,
                WorkItem.project_id == project_id,
                Evaluation.run_id.in_(run_ids),
            )
        )
        labels: dict[UUID, tuple[str | None, str]] = {}
        by_work_key = {work.work_key: work for work in works}
        for run_id, business_work_key, work_item_type in rows:
            work = (
                by_work_key.get(business_work_key)
                if business_work_key is not None
                else by_work_item_type.get(work_item_type)
            )
            if work is not None:
                labels[run_id] = (work.work_key, work.name)
        return labels

    @staticmethod
    def _overview_run(
        summary: RunSummary,
        *,
        work_key: str | None,
        work_name: str,
    ) -> ProjectOverviewRun:
        return ProjectOverviewRun(
            run_id=summary.run_id,
            business_work_key=work_key,
            business_work_name=work_name,
            status=summary.status,
            strategy_version_id=summary.strategy_version_id,
            event_count=summary.event_count,
            task_count=summary.task_count,
            operator_name=summary.operator_name,
            created_at=summary.created_at,
            started_at=summary.started_at,
            completed_at=summary.completed_at,
            failure_reason=summary.failure_reason,
            cancel_reason=summary.cancel_reason,
        )
