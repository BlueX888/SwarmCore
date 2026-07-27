from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from typing import Any, Iterable, Literal, Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_domain import uuid7
from swarmcore_persistence.models import (
    Evaluation,
    InvoiceAssuranceBatch,
    InvoiceAssuranceBatchItem,
    WorkItem,
)

from .business_works import BusinessWorkService
from .cases import CaseSubjectInput

TrendBucket = Literal["day", "week", "month"]


@dataclass(frozen=True, slots=True)
class InvoiceBatchInput:
    payload: dict[str, Any]
    subjects: tuple[CaseSubjectInput, ...]
    owner: str | None = None


@dataclass(frozen=True, slots=True)
class InvoiceBatchItemSnapshot:
    ordinal: int
    case_id: UUID
    evaluation_id: UUID
    status: str
    outcome: str | None


@dataclass(frozen=True, slots=True)
class InvoiceBatchSnapshot:
    batch_id: UUID
    status: str
    total_items: int
    max_parallelism: int
    requested_by: str
    created_at: datetime
    updated_at: datetime
    items: tuple[InvoiceBatchItemSnapshot, ...]


class InvoiceAssuranceOperationsService:
    def __init__(self, business_works: BusinessWorkService) -> None:
        self._business_works = business_works

    async def create_batch(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        inputs: tuple[InvoiceBatchInput, ...],
        max_parallelism: int,
        idempotency_key: str,
        actor: str,
        submitted_scopes: tuple[str, ...] = (),
        auth_context_hash: str = "unknown",
    ) -> InvoiceBatchSnapshot:
        if not inputs:
            raise ValueError("INVOICE_BATCH_EMPTY")
        if len(inputs) > 100:
            raise ValueError("INVOICE_BATCH_TOO_LARGE")
        if max_parallelism < 1 or max_parallelism > 10:
            raise ValueError("INVOICE_BATCH_PARALLELISM_INVALID")

        existing = await session.scalar(
            select(InvoiceAssuranceBatch).where(
                InvoiceAssuranceBatch.tenant_id == tenant_id,
                InvoiceAssuranceBatch.project_id == project_id,
                InvoiceAssuranceBatch.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            return await self.get_batch(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                batch_id=existing.id,
            )

        batch = InvoiceAssuranceBatch(
            id=uuid7(),
            tenant_id=tenant_id,
            project_id=project_id,
            idempotency_key=idempotency_key,
            requested_by=actor,
            total_items=len(inputs),
            max_parallelism=max_parallelism,
        )
        session.add(batch)

        for ordinal, value in enumerate(inputs, start=1):
            case, _, _ = await self._business_works.create_case(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                work_key="invoice-assurance",
                payload=value.payload,
                subjects=list(value.subjects),
                owner=value.owner,
                idempotency_key=f"{idempotency_key}:case:{ordinal}",
                actor=actor,
            )
            evaluation = await self._business_works.start_assessment(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                work_key="invoice-assurance",
                case_id=case.id,
                idempotency_key=f"{idempotency_key}:assessment:{ordinal}",
                actor=actor,
                submitted_scopes=submitted_scopes,
                auth_context_hash=auth_context_hash,
            )
            session.add(
                InvoiceAssuranceBatchItem(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    batch_id=batch.id,
                    ordinal=ordinal,
                    case_id=case.id,
                    evaluation_id=evaluation.id,
                )
            )

        await session.flush()
        return await self.get_batch(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            batch_id=batch.id,
        )

    async def get_batch(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        batch_id: UUID,
    ) -> InvoiceBatchSnapshot:
        batch = await session.scalar(
            select(InvoiceAssuranceBatch).where(
                InvoiceAssuranceBatch.id == batch_id,
                InvoiceAssuranceBatch.tenant_id == tenant_id,
                InvoiceAssuranceBatch.project_id == project_id,
            )
        )
        if batch is None:
            raise LookupError("invoice assurance batch not found")
        rows = (
            await session.execute(
                select(InvoiceAssuranceBatchItem, Evaluation)
                .join(
                    Evaluation,
                    Evaluation.id == InvoiceAssuranceBatchItem.evaluation_id,
                )
                .where(
                    InvoiceAssuranceBatchItem.batch_id == batch_id,
                    InvoiceAssuranceBatchItem.tenant_id == tenant_id,
                    InvoiceAssuranceBatchItem.project_id == project_id,
                )
                .order_by(InvoiceAssuranceBatchItem.ordinal)
            )
        ).all()
        items = tuple(
            InvoiceBatchItemSnapshot(
                ordinal=item.ordinal,
                case_id=item.case_id,
                evaluation_id=evaluation.id,
                status=evaluation.status,
                outcome=_result_outcome(evaluation.result),
            )
            for item, evaluation in rows
        )
        return InvoiceBatchSnapshot(
            batch_id=batch.id,
            status=_batch_status(item.status for item in items),
            total_items=batch.total_items,
            max_parallelism=batch.max_parallelism,
            requested_by=batch.requested_by,
            created_at=batch.created_at,
            updated_at=batch.updated_at,
            items=items,
        )

    async def rule_trends(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
        bucket: TrendBucket = "day",
    ) -> dict[str, Any]:
        query = (
            select(Evaluation)
            .join(WorkItem, WorkItem.id == Evaluation.work_item_id)
            .where(
                Evaluation.tenant_id == tenant_id,
                Evaluation.project_id == project_id,
                WorkItem.tenant_id == tenant_id,
                WorkItem.project_id == project_id,
                WorkItem.work_item_type == "invoice-assurance-case",
            )
            .order_by(Evaluation.created_at)
        )
        if date_from is not None:
            query = query.where(
                Evaluation.created_at >= datetime.combine(date_from, time.min, UTC)
            )
        if date_to is not None:
            query = query.where(
                Evaluation.created_at <= datetime.combine(date_to, time.max, UTC)
            )
        evaluations = list((await session.scalars(query)).all())
        return build_rule_trends(evaluations, bucket=bucket)


def build_rule_trends(
    evaluations: Iterable[Any],
    *,
    bucket: TrendBucket = "day",
) -> dict[str, Any]:
    if bucket not in {"day", "week", "month"}:
        raise ValueError("invalid trend bucket")
    outcomes: Counter[str] = Counter()
    rule_hits: Counter[tuple[str, str]] = Counter()
    buckets: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"assessments": 0, "ruleHits": 0, "outcomes": Counter()}
    )
    completed = 0
    for evaluation in evaluations:
        result = evaluation.result if isinstance(evaluation.result, Mapping) else None
        if result is None:
            continue
        completed += 1
        outcome = str(result.get("outcome") or "UNKNOWN")
        outcomes[outcome] += 1
        key = _bucket_key(evaluation.created_at, bucket)
        bucket_value = buckets[key]
        bucket_value["assessments"] += 1
        bucket_value["outcomes"][outcome] += 1
        for rule in result.get("ruleResults") or []:
            if not isinstance(rule, Mapping):
                continue
            status = str(rule.get("status") or "UNKNOWN")
            if status not in {"FAIL", "WARN", "UNKNOWN"}:
                continue
            rule_id = str(rule.get("ruleId") or "UNSPECIFIED")
            rule_hits[(rule_id, status)] += 1
            bucket_value["ruleHits"] += 1

    return {
        "bucket": bucket,
        "totalAssessments": completed,
        "outcomes": dict(sorted(outcomes.items())),
        "buckets": [
            {
                "period": key,
                "assessments": value["assessments"],
                "ruleHits": value["ruleHits"],
                "outcomes": dict(sorted(value["outcomes"].items())),
            }
            for key, value in sorted(buckets.items())
        ],
        "topRules": [
            {"ruleId": rule_id, "status": status, "count": count}
            for (rule_id, status), count in sorted(
                rule_hits.items(),
                key=lambda item: (-item[1], item[0][0], item[0][1]),
            )
        ],
    }


def _batch_status(statuses: Iterable[str]) -> str:
    values = tuple(statuses)
    if not values:
        return "QUEUED"
    terminal = {"SUCCEEDED", "FAILED", "CANCELLED"}
    if all(value in terminal for value in values):
        return "COMPLETED" if all(value == "SUCCEEDED" for value in values) else "COMPLETED_WITH_ERRORS"
    if any(value in {"RUNNING", "WAITING_APPROVAL"} for value in values):
        return "RUNNING"
    return "QUEUED"


def _result_outcome(result: Mapping[str, Any] | None) -> str | None:
    if not isinstance(result, Mapping):
        return None
    value = result.get("outcome")
    return str(value) if value is not None else None


def _bucket_key(value: datetime, bucket: TrendBucket) -> str:
    day = value.astimezone(UTC).date()
    if bucket == "day":
        return day.isoformat()
    if bucket == "week":
        year, week, _ = day.isocalendar()
        return f"{year}-W{week:02d}"
    return day.strftime("%Y-%m")
