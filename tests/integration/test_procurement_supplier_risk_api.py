from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from runtime_harness import RuntimeHarness
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine
from swarmcore_api.business_routes import capability_packs
from swarmcore_application import (
    AgentRuntimeStatus,
    CapabilityCenterService,
    CapabilityReadinessService,
    ModelRuntimeStatus,
    ProcurementSupplierRiskService,
    ToolRuntimeStatus,
    calculate_supplier_performance,
    collect_risk_observations,
    compare_procurement_clauses,
    decide_supplier_risk,
    diff_supplier_risk_snapshots,
    finalize_procurement_supplier_risk,
)
from swarmcore_persistence import tenant_transaction
from swarmcore_persistence.models import (
    CapabilityPackVersion,
    Evaluation,
    Run,
    StrategyVersion,
    WorkItemRevision,
)
from swarmcore_registry import builtin_registry


class ReadyRuntime:
    async def inspect_tool(self, **_: object) -> ToolRuntimeStatus:
        return ToolRuntimeStatus(executor_registered=True, healthy=True)

    async def inspect_model(self, **_: object) -> ModelRuntimeStatus:
        return ModelRuntimeStatus(
            route_registered=True,
            secret_available=True,
            endpoint_healthy=True,
        )

    async def inspect_agent(self, **_: object) -> AgentRuntimeStatus:
        return AgentRuntimeStatus(adapter_available=True)


@pytest.mark.asyncio
async def test_supplier_risk_monitor_is_idempotent_and_tenant_scoped(
    runtime_harness: RuntimeHarness,
) -> None:
    runtime = ReadyRuntime()
    capability_packs.attach_readiness(
        CapabilityCenterService(
            builtin_registry(),
            CapabilityReadinessService(tools=runtime, models=runtime, agents=runtime),
        ),
        environment="development",
    )
    packs = runtime_harness.api.get(
        runtime_harness.project_url("capability-packs"),
        headers=runtime_harness.headers,
    )
    assert packs.status_code == 200, packs.text
    pack = next(
        item
        for item in packs.json()["items"]
        if item["name"] == "procurement-supplier-risk"
    )
    enabled = runtime_harness.api.post(
        runtime_harness.project_url(
            f"capability-packs/{pack['versionId']}:enable"
        ),
        headers={
            **runtime_harness.headers,
            "Idempotency-Key": "enable-supplier-risk",
        },
        json={"configuration": {}},
    )
    assert enabled.status_code == 200, enabled.text

    procurement = _create_business_object(
        runtime_harness,
        object_type="procurement",
        canonical_key="PROC-INT-001",
        schema_ref="schema://procurement/facts@1",
        data={"projectNo": "PROC-INT-001"},
    )
    supplier = _create_business_object(
        runtime_harness,
        object_type="supplier",
        canonical_key="91310116740594799B",
        schema_ref="schema://supplier/facts@1",
        data={
            "name": "上海龙田数码科技有限公司",
            "creditCode": "91310116740594799B",
        },
    )
    case = runtime_harness.api.post(
        runtime_harness.project_url("cases"),
        headers={
            **runtime_harness.headers,
            "Idempotency-Key": "supplier-risk-case",
        },
        json={
            "scenarioType": "procurement-supplier-risk-case",
            "payload": {
                "title": "集成测试采购项目",
                "projectNo": "PROC-INT-001",
                "lotNo": "LOT-01",
                "procurementType": "ENTERPRISE",
                "asOf": "2026-07-28",
                "supplier": {
                    "name": "上海龙田数码科技有限公司",
                    "creditCode": "91310116740594799B",
                },
            },
            "subjects": [
                {
                    "businessObjectId": procurement["businessObjectId"],
                    "businessObjectVersionId": procurement["versionId"],
                    "role": "PRIMARY",
                    "subjectKey": "procurement",
                },
                {
                    "businessObjectId": supplier["businessObjectId"],
                    "businessObjectVersionId": supplier["versionId"],
                    "role": "RELATED",
                    "subjectKey": "supplier",
                },
            ],
        },
    )
    assert case.status_code == 201, case.text

    create_payload = {
        "caseId": case.json()["caseId"],
        "supplierName": "上海龙田数码科技有限公司",
        "supplierCreditCode": "91310116740594799B",
        "cadence": "DAILY",
        "sources": [
            {
                "kind": "CCGP_SERIOUS_ILLEGAL",
                "sourceRef": "official://ccgp/serious-illegal",
            }
        ],
    }
    headers = {
        **runtime_harness.headers,
        "Idempotency-Key": "supplier-risk-monitor",
    }
    created = runtime_harness.api.post(
        runtime_harness.project_url("procurement-supplier-risk/monitors"),
        headers=headers,
        json=create_payload,
    )
    replayed = runtime_harness.api.post(
        runtime_harness.project_url("procurement-supplier-risk/monitors"),
        headers=headers,
        json=create_payload,
    )
    assert created.status_code == 201, created.text
    assert replayed.status_code == 201, replayed.text
    assert replayed.json()["monitorId"] == created.json()["monitorId"]
    monitor_id = created.json()["monitorId"]

    fetched = runtime_harness.api.get(
        runtime_harness.project_url(
            f"procurement-supplier-risk/monitors/{monitor_id}"
        ),
        headers=runtime_harness.headers,
    )
    history = runtime_harness.api.get(
        runtime_harness.project_url(
            f"procurement-supplier-risk/monitors/{monitor_id}/history"
        ),
        headers=runtime_harness.headers,
    )
    alerts = runtime_harness.api.get(
        runtime_harness.project_url("procurement-supplier-risk/alerts"),
        headers=runtime_harness.headers,
        params={"monitorId": monitor_id},
    )
    work_orders = runtime_harness.api.get(
        runtime_harness.project_url("procurement-supplier-risk/work-orders"),
        headers=runtime_harness.headers,
        params={"monitorId": monitor_id},
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["supplierCreditCode"] == "91310116740594799B"
    assert history.json()["items"] == []
    assert alerts.json()["items"] == []
    assert work_orders.json()["items"] == []

    result = _blocking_result(
        case_id=case.json()["caseId"],
        monitor_id=monitor_id,
    )
    async with tenant_transaction(
        runtime_harness.database.sessions,
        tenant_id=runtime_harness.tenant_id,
        project_id=runtime_harness.project_id,
    ) as session:
        revision = await session.scalar(
            select(WorkItemRevision)
            .where(WorkItemRevision.work_item_id == UUID(case.json()["caseId"]))
            .order_by(WorkItemRevision.revision.desc())
            .limit(1)
        )
        pack_version = await session.get(
            CapabilityPackVersion,
            UUID(pack["versionId"]),
        )
        assert revision is not None
        assert pack_version is not None
        strategy_id = UUID(
            pack_version.dependency_snapshot["strategy"]["strategyVersionId"]
        )
        strategy = await session.get(StrategyVersion, strategy_id)
        assert strategy is not None
        run = Run(
            tenant_id=runtime_harness.tenant_id,
            project_id=runtime_harness.project_id,
            strategy_version_id=strategy.id,
            status="SUCCEEDED",
            input={},
            output=result,
            budgets={},
            usage={},
            plan_hash=strategy.plan_hash,
            runtime_version=strategy.runtime_version,
            temporal_workflow_id=f"integration-supplier-risk-{uuid4()}",
            initiated_by="integration",
            submitted_scopes=[],
            auth_context_hash="0" * 64,
            policy_revision="integration",
        )
        session.add(run)
        await session.flush()
        evaluation = Evaluation(
            tenant_id=runtime_harness.tenant_id,
            project_id=runtime_harness.project_id,
            work_item_id=UUID(case.json()["caseId"]),
            work_item_revision_id=revision.id,
            capability_pack_version_id=pack_version.id,
            run_id=run.id,
            idempotency_key=f"integration-evaluation-{uuid4()}",
            request_hash="1" * 64,
            status="SUCCEEDED",
            result=result,
            strategy_version_id=strategy.id,
            plan_hash=strategy.plan_hash,
            registry_snapshot={},
            attachment_manifest_hash="2" * 64,
            input_schema_version="schema://procurement-supplier-risk/input@1",
            output_schema_version="schema://procurement-supplier-risk/result@1",
            report_template_version="report://procurement-supplier-risk@1",
            policy_revision="integration",
        )
        session.add(evaluation)
        await session.flush()
        snapshot, snapshot_alerts = await ProcurementSupplierRiskService().record_snapshot(
            session,
            tenant_id=runtime_harness.tenant_id,
            project_id=runtime_harness.project_id,
            monitor_id=UUID(monitor_id),
            evaluation_id=evaluation.id,
            result=result,
            actor="integration",
        )
        snapshot_id = snapshot.id
        assert {item.alert_type for item in snapshot_alerts} == {
            "HARD_GATE",
            "MATERIAL_CLAUSE_DEVIATION",
        }

    history = runtime_harness.api.get(
        runtime_harness.project_url(
            f"procurement-supplier-risk/monitors/{monitor_id}/history"
        ),
        headers=runtime_harness.headers,
    )
    alerts = runtime_harness.api.get(
        runtime_harness.project_url("procurement-supplier-risk/alerts"),
        headers=runtime_harness.headers,
        params={"monitorId": monitor_id},
    )
    assert history.json()["items"][0]["decision"] == "BLOCK"
    assert len(alerts.json()["items"]) == 2
    alert_id = alerts.json()["items"][0]["alertId"]

    create_order = runtime_harness.api.post(
        runtime_harness.project_url(
            f"procurement-supplier-risk/alerts/{alert_id}/work-orders"
        ),
        headers={
            **runtime_harness.headers,
            "Idempotency-Key": "supplier-risk-work-order",
        },
        json={"priority": "CRITICAL", "assignee": "risk-owner"},
    )
    replayed_order = runtime_harness.api.post(
        runtime_harness.project_url(
            f"procurement-supplier-risk/alerts/{alert_id}/work-orders"
        ),
        headers={
            **runtime_harness.headers,
            "Idempotency-Key": "supplier-risk-work-order",
        },
        json={"priority": "CRITICAL", "assignee": "risk-owner"},
    )
    assert create_order.status_code == 201, create_order.text
    assert replayed_order.json()["workOrderId"] == create_order.json()["workOrderId"]
    work_order_id = create_order.json()["workOrderId"]

    started = runtime_harness.api.patch(
        runtime_harness.project_url(
            f"procurement-supplier-risk/work-orders/{work_order_id}"
        ),
        headers=runtime_harness.headers,
        json={
            "status": "IN_PROGRESS",
            "comment": "开始核验处罚记录",
        },
    )
    closed = runtime_harness.api.patch(
        runtime_harness.project_url(
            f"procurement-supplier-risk/work-orders/{work_order_id}"
        ),
        headers=runtime_harness.headers,
        json={
            "status": "CLOSED",
            "resolution": {"outcome": "blocked", "approvedBy": "risk-owner"},
            "comment": "已阻断供应商准入",
        },
    )
    assert started.status_code == 200, started.text
    assert closed.status_code == 200, closed.text
    assert closed.json()["status"] == "CLOSED"
    assert [item["action"] for item in closed.json()["actions"]] == [
        "CREATE",
        "TRANSITION",
        "TRANSITION",
    ]

    engine = create_async_engine(runtime_harness.database_url)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            await connection.execute(
                text("SELECT set_config('app.tenant_id', :value, true)"),
                {"value": str(runtime_harness.tenant_id)},
            )
            await connection.execute(
                text("SELECT set_config('app.project_id', :value, true)"),
                {"value": str(runtime_harness.project_id)},
            )
            with pytest.raises(DBAPIError, match="immutable"):
                await connection.execute(
                    text(
                        "UPDATE supplier_risk_snapshots "
                        "SET decision = 'PASS' WHERE id = :snapshot_id"
                    ),
                    {"snapshot_id": snapshot_id},
                )
            await transaction.rollback()
    finally:
        await engine.dispose()

    hidden = runtime_harness.api.get(
        runtime_harness.project_url(
            f"procurement-supplier-risk/monitors/{monitor_id}"
        ),
        headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000099"},
    )
    assert hidden.status_code == 404


def _create_business_object(
    runtime_harness: RuntimeHarness,
    *,
    object_type: str,
    canonical_key: str,
    schema_ref: str,
    data: dict[str, str],
) -> dict[str, str]:
    response = runtime_harness.api.post(
        runtime_harness.project_url("business-objects"),
        headers={
            **runtime_harness.headers,
            "Idempotency-Key": f"business-object-{canonical_key}",
        },
        json={
            "objectType": object_type,
            "canonicalKey": canonical_key,
            "schemaRef": schema_ref,
            "data": data,
            "provenance": {"source": "integration"},
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _blocking_result(*, case_id: str, monitor_id: str) -> dict[str, object]:
    supplier = {
        "name": "上海龙田数码科技有限公司",
        "creditCode": "91310116740594799B",
    }
    consistency = compare_procurement_clauses(
        {
            "clauses": {
                stage: [
                    {
                        "matchKey": "price",
                        "category": "PRICE",
                        "text": text_value,
                        "evidenceRefs": [
                            {"documentId": stage.lower(), "page": 1}
                        ],
                    }
                ]
                for stage, text_value in {
                    "TENDER": "合同总价100万元",
                    "BID": "合同总价100万元",
                    "AWARD": "合同总价100万元",
                    "CONTRACT": "合同总价120万元",
                }.items()
            }
        }
    )
    collection = collect_risk_observations(
        {
            "supplier": supplier,
            "sources": [
                {
                    "sourceRef": "official://ccgp/serious-illegal",
                    "status": "SUCCEEDED",
                    "records": [
                        {
                            "sourceRecordId": "ccgp-record-001",
                            "supplierCreditCode": supplier["creditCode"],
                            "riskType": "GOVERNMENT_PROCUREMENT_BAN",
                            "active": True,
                            "effectiveFrom": "2026-07-12",
                            "effectiveTo": "2027-07-12",
                            "evidenceRefs": [
                                {
                                    "sourceUrl": "https://www.ccgp.gov.cn/cr/list",
                                    "recordId": "ccgp-record-001",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    )
    performance = calculate_supplier_performance(
        {
            "records": [
                {
                    "orderId": f"PO-{index}",
                    "plannedDeliveryAt": "2026-07-10",
                    "actualDeliveryAt": "2026-07-09",
                    "qualityPassedQty": 100,
                    "qualityInspectedQty": 100,
                    "acceptanceSlaMet": True,
                    "serviceSlaMet": True,
                    "commercialCompliant": True,
                    "complaints": 0,
                    "resolvedComplaints": 0,
                    "rectificationOnTime": True,
                }
                for index in range(1, 4)
            ]
        }
    )
    risk = decide_supplier_risk(
        {
            "riskCollection": collection,
            "performance": performance,
            "asOf": "2026-07-28",
        }
    )
    history = diff_supplier_risk_snapshots(None, risk)
    return finalize_procurement_supplier_risk(
        {
            "caseId": case_id,
            "monitorId": monitor_id,
            "assessmentId": "integration-assessment",
            "asOf": "2026-07-28",
            "supplier": supplier,
            "consistency": consistency,
            "risk": risk,
            "performance": performance,
            "history": history,
            "provenance": {"source": "integration"},
        }
    )
