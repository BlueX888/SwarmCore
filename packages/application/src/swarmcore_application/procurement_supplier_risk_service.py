from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_persistence import AuditRepository
from swarmcore_persistence.models import (
    OutboxEvent,
    SupplierRiskAlert,
    SupplierRiskMonitor,
    SupplierRiskSnapshot,
    SupplierRiskWorkOrder,
    SupplierRiskWorkOrderAction,
    WorkItem,
)
from swarmcore_persistence.repositories import canonical_hash

from .procurement_supplier_risk import (
    diff_supplier_risk_snapshots,
    validate_procurement_supplier_risk_result,
)

_WORK_ORDER_TRANSITIONS: dict[str, frozenset[str]] = {
    "OPEN": frozenset({"IN_PROGRESS", "REJECTED", "CLOSED"}),
    "IN_PROGRESS": frozenset({"RESOLVED", "REJECTED", "CLOSED"}),
    "RESOLVED": frozenset({"IN_PROGRESS", "CLOSED"}),
    "REJECTED": frozenset(),
    "CLOSED": frozenset(),
}


class ProcurementSupplierRiskService:
    async def create_monitor(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        case_id: UUID,
        supplier_name: str,
        supplier_credit_code: str,
        cadence: str,
        source_configuration: Sequence[Mapping[str, Any]],
        idempotency_key: str,
        actor: str,
    ) -> SupplierRiskMonitor:
        normalized_code = supplier_credit_code.strip().upper()
        if not normalized_code:
            raise ValueError("SUPPLIER_CREDIT_CODE_REQUIRED")
        request_hash = canonical_hash(
            {
                "caseId": str(case_id),
                "supplierName": supplier_name.strip(),
                "supplierCreditCode": normalized_code,
                "cadence": cadence.upper(),
                "sourceConfiguration": list(source_configuration),
            }
        )
        existing = await session.scalar(
            select(SupplierRiskMonitor).where(
                SupplierRiskMonitor.tenant_id == tenant_id,
                SupplierRiskMonitor.project_id == project_id,
                SupplierRiskMonitor.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            if existing.request_hash != request_hash:
                raise ValueError("IDEMPOTENCY_KEY_REUSED")
            return existing
        case = await session.scalar(
            select(WorkItem).where(
                WorkItem.tenant_id == tenant_id,
                WorkItem.project_id == project_id,
                WorkItem.id == case_id,
            )
        )
        if case is None:
            raise LookupError("PROCUREMENT_SUPPLIER_RISK_CASE_NOT_FOUND")
        if case.work_item_type != "procurement-supplier-risk-case":
            raise ValueError("CASE_TYPE_MISMATCH")
        value = SupplierRiskMonitor(
            tenant_id=tenant_id,
            project_id=project_id,
            case_id=case_id,
            supplier_name=supplier_name.strip(),
            supplier_credit_code=normalized_code,
            cadence=cadence.upper(),
            source_configuration=[dict(item) for item in source_configuration],
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            created_by=actor,
        )
        session.add(value)
        await session.flush()
        await self._audit(
            session,
            value=value,
            actor=actor,
            action="supplier-risk.monitor.create",
            metadata={"requestHash": request_hash, "caseId": str(case_id)},
        )
        return value

    async def get_monitor(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        monitor_id: UUID,
    ) -> SupplierRiskMonitor:
        value = await session.scalar(
            select(SupplierRiskMonitor).where(
                SupplierRiskMonitor.tenant_id == tenant_id,
                SupplierRiskMonitor.project_id == project_id,
                SupplierRiskMonitor.id == monitor_id,
            )
        )
        if value is None:
            raise LookupError("SUPPLIER_RISK_MONITOR_NOT_FOUND")
        return value

    async def list_snapshots(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        monitor_id: UUID,
        limit: int = 100,
    ) -> list[SupplierRiskSnapshot]:
        await self.get_monitor(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            monitor_id=monitor_id,
        )
        return list(
            await session.scalars(
                select(SupplierRiskSnapshot)
                .where(
                    SupplierRiskSnapshot.tenant_id == tenant_id,
                    SupplierRiskSnapshot.project_id == project_id,
                    SupplierRiskSnapshot.monitor_id == monitor_id,
                )
                .order_by(
                    SupplierRiskSnapshot.as_of.desc(),
                    SupplierRiskSnapshot.created_at.desc(),
                )
                .limit(limit)
            )
        )

    async def list_alerts(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        monitor_id: UUID | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[SupplierRiskAlert]:
        query = select(SupplierRiskAlert).where(
            SupplierRiskAlert.tenant_id == tenant_id,
            SupplierRiskAlert.project_id == project_id,
        )
        if monitor_id is not None:
            query = query.where(SupplierRiskAlert.monitor_id == monitor_id)
        if status is not None:
            query = query.where(SupplierRiskAlert.status == status.upper())
        return list(
            await session.scalars(
                query.order_by(SupplierRiskAlert.created_at.desc()).limit(limit)
            )
        )

    async def record_snapshot(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        monitor_id: UUID,
        evaluation_id: UUID,
        result: Mapping[str, Any],
        actor: str,
    ) -> tuple[SupplierRiskSnapshot, list[SupplierRiskAlert]]:
        monitor = await self.get_monitor(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            monitor_id=monitor_id,
        )
        normalized = validate_procurement_supplier_risk_result(dict(result))
        result_hash = str(normalized["resultHash"])
        existing = await session.scalar(
            select(SupplierRiskSnapshot).where(
                SupplierRiskSnapshot.monitor_id == monitor_id,
                SupplierRiskSnapshot.result_hash == result_hash,
            )
        )
        if existing is not None:
            alerts = list(
                await session.scalars(
                    select(SupplierRiskAlert).where(
                        SupplierRiskAlert.snapshot_id == existing.id
                    )
                )
            )
            return existing, alerts
        previous = await session.scalar(
            select(SupplierRiskSnapshot)
            .where(
                SupplierRiskSnapshot.tenant_id == tenant_id,
                SupplierRiskSnapshot.project_id == project_id,
                SupplierRiskSnapshot.monitor_id == monitor_id,
            )
            .order_by(
                SupplierRiskSnapshot.as_of.desc(),
                SupplierRiskSnapshot.created_at.desc(),
            )
            .limit(1)
        )
        current_risk = dict(normalized.get("risk") or {})
        previous_risk = dict(previous.result.get("risk") or {}) if previous is not None else None
        history = diff_supplier_risk_snapshots(previous_risk, current_risk)
        raw_as_of = current_risk.get("asOf") or normalized.get("asOf")
        as_of = self._parse_datetime(raw_as_of)
        snapshot = SupplierRiskSnapshot(
            tenant_id=tenant_id,
            project_id=project_id,
            monitor_id=monitor_id,
            evaluation_id=evaluation_id,
            as_of=as_of,
            decision=str(normalized["decision"]),
            risk_level=str(normalized["riskLevel"]),
            risk_score=int(float(current_risk.get("overallRiskScore") or 0)),
            source_coverage={
                "coverage": current_risk.get("dataCoverage"),
                "sources": list(current_risk.get("sourceStatuses") or []),
            },
            change_summary=history,
            result=normalized,
            result_hash=result_hash,
        )
        session.add(snapshot)
        await session.flush()
        alerts = await self._create_snapshot_alerts(
            session,
            monitor=monitor,
            snapshot=snapshot,
            result=normalized,
            history=history,
        )
        monitor.last_snapshot_id = snapshot.id
        monitor.last_checked_at = datetime.now(UTC)
        await self._audit(
            session,
            value=monitor,
            actor=actor,
            action="supplier-risk.snapshot.record",
            metadata={
                "snapshotId": str(snapshot.id),
                "resultHash": result_hash,
                "alertIds": [str(item.id) for item in alerts],
            },
        )
        return snapshot, alerts

    async def create_work_order(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        alert_id: UUID,
        priority: str,
        assignee: str | None,
        due_at: datetime | None,
        idempotency_key: str,
        actor: str,
    ) -> SupplierRiskWorkOrder:
        request_hash = canonical_hash(
            {
                "alertId": str(alert_id),
                "priority": priority.upper(),
                "assignee": assignee,
                "dueAt": due_at.isoformat() if due_at else None,
            }
        )
        existing = await session.scalar(
            select(SupplierRiskWorkOrder).where(
                SupplierRiskWorkOrder.tenant_id == tenant_id,
                SupplierRiskWorkOrder.project_id == project_id,
                SupplierRiskWorkOrder.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            if existing.request_hash != request_hash:
                raise ValueError("IDEMPOTENCY_KEY_REUSED")
            return existing
        alert = await session.scalar(
            select(SupplierRiskAlert).where(
                SupplierRiskAlert.tenant_id == tenant_id,
                SupplierRiskAlert.project_id == project_id,
                SupplierRiskAlert.id == alert_id,
            )
        )
        if alert is None:
            raise LookupError("SUPPLIER_RISK_ALERT_NOT_FOUND")
        value = SupplierRiskWorkOrder(
            tenant_id=tenant_id,
            project_id=project_id,
            alert_id=alert_id,
            priority=priority.upper(),
            assignee=assignee,
            due_at=due_at,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            created_by=actor,
        )
        session.add(value)
        await session.flush()
        session.add(
            SupplierRiskWorkOrderAction(
                tenant_id=tenant_id,
                project_id=project_id,
                work_order_id=value.id,
                action="CREATE",
                from_status=None,
                to_status="OPEN",
                actor=actor,
                metadata_={"alertId": str(alert_id)},
            )
        )
        alert.status = "IN_REVIEW"
        await self._audit(
            session,
            value=value,
            actor=actor,
            action="supplier-risk.work-order.create",
            metadata={"alertId": str(alert_id), "requestHash": request_hash},
        )
        return value

    async def update_work_order(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_order_id: UUID,
        status: str,
        assignee: str | None,
        resolution: Mapping[str, Any] | None,
        comment: str | None,
        actor: str,
    ) -> SupplierRiskWorkOrder:
        value = await session.scalar(
            select(SupplierRiskWorkOrder)
            .where(
                SupplierRiskWorkOrder.tenant_id == tenant_id,
                SupplierRiskWorkOrder.project_id == project_id,
                SupplierRiskWorkOrder.id == work_order_id,
            )
            .with_for_update()
        )
        if value is None:
            raise LookupError("SUPPLIER_RISK_WORK_ORDER_NOT_FOUND")
        target = status.upper()
        if target != value.status and target not in _WORK_ORDER_TRANSITIONS[value.status]:
            raise ValueError(f"INVALID_WORK_ORDER_TRANSITION:{value.status}->{target}")
        if target in {"RESOLVED", "CLOSED"} and not resolution:
            raise ValueError("WORK_ORDER_RESOLUTION_REQUIRED")
        before = value.status
        value.status = target
        if assignee is not None:
            value.assignee = assignee
        if resolution is not None:
            value.resolution = dict(resolution)
        session.add(
            SupplierRiskWorkOrderAction(
                tenant_id=tenant_id,
                project_id=project_id,
                work_order_id=value.id,
                action="TRANSITION" if target != before else "UPDATE",
                from_status=before,
                to_status=target,
                comment=comment,
                actor=actor,
                metadata_={"assignee": value.assignee},
            )
        )
        if target == "CLOSED":
            alert = await session.scalar(
                select(SupplierRiskAlert).where(SupplierRiskAlert.id == value.alert_id)
            )
            if alert is not None:
                alert.status = "CLOSED"
                alert.acknowledged_by = actor
                alert.acknowledged_at = datetime.now(UTC)
        await self._audit(
            session,
            value=value,
            actor=actor,
            action="supplier-risk.work-order.update",
            metadata={"from": before, "to": target, "comment": comment},
        )
        return value

    async def list_work_order_actions(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        work_order_id: UUID,
    ) -> list[SupplierRiskWorkOrderAction]:
        return list(
            await session.scalars(
                select(SupplierRiskWorkOrderAction)
                .where(
                    SupplierRiskWorkOrderAction.tenant_id == tenant_id,
                    SupplierRiskWorkOrderAction.project_id == project_id,
                    SupplierRiskWorkOrderAction.work_order_id == work_order_id,
                )
                .order_by(SupplierRiskWorkOrderAction.created_at)
            )
        )

    async def list_work_orders(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        monitor_id: UUID | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[SupplierRiskWorkOrder]:
        query = select(SupplierRiskWorkOrder).where(
            SupplierRiskWorkOrder.tenant_id == tenant_id,
            SupplierRiskWorkOrder.project_id == project_id,
        )
        if monitor_id is not None:
            query = query.join(
                SupplierRiskAlert,
                SupplierRiskAlert.id == SupplierRiskWorkOrder.alert_id,
            ).where(SupplierRiskAlert.monitor_id == monitor_id)
        if status is not None:
            query = query.where(SupplierRiskWorkOrder.status == status.upper())
        return list(
            await session.scalars(
                query.order_by(SupplierRiskWorkOrder.updated_at.desc()).limit(limit)
            )
        )

    async def _create_snapshot_alerts(
        self,
        session: AsyncSession,
        *,
        monitor: SupplierRiskMonitor,
        snapshot: SupplierRiskSnapshot,
        result: dict[str, Any],
        history: dict[str, Any],
    ) -> list[SupplierRiskAlert]:
        candidates: list[dict[str, Any]] = []
        risk = dict(result.get("risk") or {})
        for gate in risk.get("hardGates") or []:
            candidates.append(
                {
                    "type": "HARD_GATE",
                    "severity": "CRITICAL",
                    "title": f"供应商命中准入阻断规则: {gate.get('code')}",
                    "details": dict(gate),
                    "evidence": list(gate.get("evidenceRefs") or []),
                    "suffix": f"{gate.get('code')}:{gate.get('sourceRecordId')}",
                }
            )
        consistency = dict(result.get("consistency") or {})
        if consistency.get("blocking"):
            candidates.append(
                {
                    "type": "MATERIAL_CLAUSE_DEVIATION",
                    "severity": "HIGH",
                    "title": "招采与合同存在重大条款差异",
                    "details": {"counts": consistency.get("counts")},
                    "evidence": list(consistency.get("evidenceRefs") or []),
                    "suffix": "consistency",
                }
            )
        if history.get("hasMaterialChange"):
            candidates.append(
                {
                    "type": "RISK_CHANGE",
                    "severity": "HIGH",
                    "title": "供应商风险状态发生实质变化",
                    "details": history,
                    "evidence": [],
                    "suffix": "history",
                }
            )
        alerts: list[SupplierRiskAlert] = []
        for candidate in candidates:
            dedupe_key = canonical_hash(
                {
                    "resultHash": snapshot.result_hash,
                    "type": candidate["type"],
                    "suffix": candidate["suffix"],
                }
            )
            alert = SupplierRiskAlert(
                tenant_id=monitor.tenant_id,
                project_id=monitor.project_id,
                monitor_id=monitor.id,
                snapshot_id=snapshot.id,
                alert_type=candidate["type"],
                severity=candidate["severity"],
                title=candidate["title"],
                details=candidate["details"],
                evidence=candidate["evidence"],
                dedupe_key=dedupe_key,
            )
            session.add(alert)
            await session.flush()
            alerts.append(alert)
            session.add(
                OutboxEvent(
                    tenant_id=monitor.tenant_id,
                    aggregate_id=monitor.id,
                    destination="nats",
                    partition_key=str(monitor.id),
                    source_id=alert.id,
                    type="supplier.risk.alert.created",
                    payload={
                        "projectId": str(monitor.project_id),
                        "monitorId": str(monitor.id),
                        "snapshotId": str(snapshot.id),
                        "alertId": str(alert.id),
                        "type": alert.alert_type,
                        "severity": alert.severity,
                    },
                )
            )
        return alerts

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        if isinstance(value, str) and value:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        return datetime.now(UTC)

    @staticmethod
    async def _audit(
        session: AsyncSession,
        *,
        value: SupplierRiskMonitor | SupplierRiskWorkOrder,
        actor: str,
        action: str,
        metadata: dict[str, Any],
    ) -> None:
        await AuditRepository().append(
            session,
            tenant_id=value.tenant_id,
            project_id=value.project_id,
            actor_id=actor,
            action=action,
            resource_type=value.__tablename__,
            resource_id=str(value.id),
            metadata=metadata,
        )


__all__ = ["ProcurementSupplierRiskService"]
