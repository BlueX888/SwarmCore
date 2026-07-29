from __future__ import annotations

import base64

import pytest
from swarmcore_application import capability_tool_executors as executors_module
from swarmcore_application.capability_tool_executors import (
    SupplierRiskCollectExecutor,
    procurement_consistency_compare,
    procurement_supplier_risk_finalize,
    procurement_supplier_risk_report_render,
    supplier_history_diff,
    supplier_performance_calculate,
    supplier_risk_decide,
)


@pytest.mark.asyncio
async def test_procurement_supplier_risk_tools_run_real_input_pipeline() -> None:
    supplier = {"name": "华东测试设备有限公司", "creditCode": "91310000TEST001"}
    consistency = await procurement_consistency_compare(
        {
            "clauseLineage": [
                {
                    "clauseKey": "PAYMENT",
                    "title": "付款条件",
                    "material": True,
                    "stages": {
                        "TENDER": {
                            "text": "验收后30日内付款",
                            "evidenceRefs": [{"documentId": "tender", "page": 12}],
                        },
                        "BID": {
                            "text": "验收后30日内付款",
                            "evidenceRefs": [{"documentId": "bid", "page": 8}],
                        },
                        "AWARD": {
                            "text": "验收后30日内付款",
                            "evidenceRefs": [{"documentId": "award", "page": 2}],
                        },
                        "CONTRACT": {
                            "text": "验收后60日内付款",
                            "evidenceRefs": [{"documentId": "contract", "page": 15}],
                        },
                    },
                }
            ]
        },
        "effect-consistency",
    )
    collection = await SupplierRiskCollectExecutor().execute(
        {
            "supplier": supplier,
            "asOf": "2026-07-28",
            "sources": [
                {
                    "sourceRef": "internal://supplier-blacklist",
                    "status": "SUCCEEDED",
                    "fetchedAt": "2026-07-28T08:00:00+08:00",
                    "records": [
                        {
                            "sourceRecordId": "blacklist-001",
                            "supplierCreditCode": supplier["creditCode"],
                            "riskType": "INTERNAL_BLACKLIST",
                            "active": True,
                            "evidenceRefs": [{"recordId": "blacklist-001"}],
                        }
                    ],
                }
            ],
        },
        "effect-collect",
        None,
    )
    performance = await supplier_performance_calculate(
        {
            "records": [
                {
                    "orderId": f"PO-{index}",
                    "plannedDeliveryAt": "2026-07-10",
                    "actualDeliveryAt": "2026-07-09",
                    "qualityPassedQty": 98,
                    "qualityInspectedQty": 100,
                    "acceptanceSlaMet": True,
                    "serviceSlaMet": True,
                    "commercialCompliant": True,
                    "complaints": 1,
                    "resolvedComplaints": 1,
                    "rectificationOnTime": True,
                    "sourceRecordRef": f"erp://PO-{index}",
                }
                for index in range(1, 4)
            ]
        },
        "effect-performance",
    )
    risk = await supplier_risk_decide(
        {
            "riskCollection": collection,
            "performance": performance,
            "asOf": "2026-07-28",
        },
        "effect-risk",
    )
    history = await supplier_history_diff(
        {"previous": None, "current": risk}, "effect-history"
    )
    result = await procurement_supplier_risk_finalize(
        {
            "caseId": "case-1",
            "assessmentId": "assessment-1",
            "asOf": "2026-07-28",
            "supplier": supplier,
            "consistency": consistency,
            "risk": risk,
            "performance": performance,
            "history": history,
            "provenance": {"inputSource": "unit-test-business-records"},
        },
        "effect-finalize",
    )
    rendered = await procurement_supplier_risk_report_render(
        {"result": result}, "effect-report"
    )

    assert collection["collectionStatus"] == "COMPLETE"
    assert collection["observations"][0]["identityMatch"] == "EXACT_CREDIT_CODE"
    assert risk["decision"] == "BLOCK"
    assert risk["hardGates"][0]["code"] == "INTERNAL_BLACKLIST"
    assert result["decision"] == "BLOCK"
    assert result["resultHash"]
    assert base64.b64decode(rendered["contentBase64"]).startswith(b"%PDF")


@pytest.mark.asyncio
async def test_supplier_risk_http_failure_is_explicit_and_never_faked() -> None:
    result = await SupplierRiskCollectExecutor().execute(
        {
            "supplier": {"name": "测试供应商", "creditCode": "91310000TEST002"},
            "sources": [
                {
                    "sourceRef": "untrusted",
                    "endpoint": "https://example.com/risk",
                }
            ],
        },
        "effect",
        None,
    )

    assert result["collectionStatus"] == "FAILED"
    assert result["observations"] == []
    assert result["sourceStatuses"][0]["status"] == "FAILED"


@pytest.mark.asyncio
async def test_supplier_risk_rejects_redirects_outside_the_allowlist(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Response:
        def __enter__(self) -> Response:
            return self

        def __exit__(self, *args: object) -> None:
            del args

        def geturl(self) -> str:
            return "https://redirected.example.net/records"

        def read(self, _limit: int) -> bytes:
            return b'{"records":[]}'

    monkeypatch.setattr(executors_module, "urlopen", lambda *_args, **_kwargs: Response())
    result = await SupplierRiskCollectExecutor(
        allowed_hosts=("api.example.com",)
    ).execute(
        {
            "supplier": {"name": "测试供应商", "creditCode": "91310000TEST003"},
            "sources": [
                {
                    "sourceRef": "authorized-provider",
                    "endpoint": "https://api.example.com/records",
                }
            ],
        },
        "effect",
        None,
    )

    assert result["collectionStatus"] == "FAILED"
    assert result["observations"] == []


@pytest.mark.asyncio
async def test_supplier_risk_collects_official_ccgp_blacklist_by_credit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    html = """
    <table>
      <tr class="trShow">
        <td>1</td>
        <td><a onclick="detail('record-001')">上海龙田数码科技有限公司</a></td>
        <td>91310116740594799B</td>
        <td>上海市普陀区</td>
        <td>串通情形</td>
        <td>罚款5792元, 列入不良行为记录名单, 十二个月内禁止参加政府采购活动</td>
        <td>《中华人民共和国政府采购法》第七十七条</td>
        <td>2026-07-12</td>
        <td>2026-07-21 16:34</td>
        <td>财政部</td>
      </tr>
    </table>
    """.encode()

    class Response:
        def __enter__(self) -> Response:
            return self

        def __exit__(self, *args: object) -> None:
            del args

        def read(self, _limit: int) -> bytes:
            return html

    monkeypatch.setattr(executors_module, "urlopen", lambda *_args, **_kwargs: Response())
    result = await SupplierRiskCollectExecutor().execute(
        {
            "supplier": {
                "name": "上海龙田数码科技有限公司",
                "creditCode": "91310116740594799B",
            },
            "asOf": "2026-07-28",
            "sources": [
                {
                    "kind": "CCGP_SERIOUS_ILLEGAL",
                    "sourceRef": "official://ccgp/serious-illegal",
                }
            ],
        },
        "effect",
        None,
    )

    assert result["collectionStatus"] == "COMPLETE"
    assert result["observations"][0]["riskType"] == "GOVERNMENT_PROCUREMENT_BAN"
    assert result["observations"][0]["identityMatch"] == "EXACT_CREDIT_CODE"
    assert result["observations"][0]["active"] is True
    assert result["observations"][0]["effectiveTo"] == "2027-07-12"
    assert result["observations"][0]["evidenceRefs"][0]["responseHash"]

    before_punishment = await SupplierRiskCollectExecutor().execute(
        {
            "supplier": {
                "name": "上海龙田数码科技有限公司",
                "creditCode": "91310116740594799B",
            },
            "asOf": "2026-01-01",
            "sources": [
                {
                    "kind": "CCGP_SERIOUS_ILLEGAL",
                    "sourceRef": "official://ccgp/serious-illegal",
                }
            ],
        },
        "effect-before",
        None,
    )
    assert before_punishment["observations"][0]["active"] is False
