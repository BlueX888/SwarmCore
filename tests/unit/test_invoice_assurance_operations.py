from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from swarmcore_application import (
    InvoiceAssuranceOperationsService,
    InvoiceBatchInput,
    InvoiceBatchSnapshot,
    build_rule_trends,
)
from swarmcore_application.cases import CaseSubjectInput


def test_rule_trends_aggregate_only_non_pass_rule_hits() -> None:
    evaluations = [
        SimpleNamespace(
            created_at=datetime(2026, 7, 26, 10, tzinfo=UTC),
            result={
                "outcome": "PAYMENT_BLOCKED",
                "ruleResults": [
                    {"ruleId": "DUPLICATE", "status": "FAIL"},
                    {"ruleId": "ARITHMETIC", "status": "PASS"},
                ],
            },
        ),
        SimpleNamespace(
            created_at=datetime(2026, 7, 27, 10, tzinfo=UTC),
            result={
                "outcome": "REVIEW_REQUIRED",
                "ruleResults": [
                    {"ruleId": "DUPLICATE", "status": "WARN"},
                    {"ruleId": "ENTERPRISE_STATUS", "status": "UNKNOWN"},
                ],
            },
        ),
    ]

    trend = build_rule_trends(evaluations, bucket="day")

    assert trend["totalAssessments"] == 2
    assert trend["outcomes"] == {
        "PAYMENT_BLOCKED": 1,
        "REVIEW_REQUIRED": 1,
    }
    assert [item["period"] for item in trend["buckets"]] == [
        "2026-07-26",
        "2026-07-27",
    ]
    assert sum(item["count"] for item in trend["topRules"]) == 3


@pytest.mark.asyncio
async def test_batch_creates_independent_cases_and_assessments() -> None:
    business_works = MagicMock()
    business_works.create_case = AsyncMock(
        side_effect=[
            (SimpleNamespace(id=uuid4()), MagicMock(), []),
            (SimpleNamespace(id=uuid4()), MagicMock(), []),
        ]
    )
    business_works.start_assessment = AsyncMock(
        side_effect=[
            SimpleNamespace(id=uuid4()),
            SimpleNamespace(id=uuid4()),
        ]
    )
    service = InvoiceAssuranceOperationsService(business_works)
    expected = InvoiceBatchSnapshot(
        batch_id=uuid4(),
        status="QUEUED",
        total_items=2,
        max_parallelism=2,
        requested_by="ap-user",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        items=(),
    )
    service.get_batch = AsyncMock(return_value=expected)  # type: ignore[method-assign]
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    subject = CaseSubjectInput(
        business_object_id=uuid4(),
        business_object_version_id=uuid4(),
        role="PRIMARY",
        subject_key="invoice",
    )

    result = await service.create_batch(
        session,
        tenant_id=uuid4(),
        project_id=uuid4(),
        inputs=(
            InvoiceBatchInput(payload={"title": "发票 1"}, subjects=(subject,)),
            InvoiceBatchInput(payload={"title": "发票 2"}, subjects=(subject,)),
        ),
        max_parallelism=2,
        idempotency_key="batch-1",
        actor="ap-user",
    )

    assert result is expected
    assert business_works.create_case.await_count == 2
    assert business_works.start_assessment.await_count == 2
    case_keys = [
        call.kwargs["idempotency_key"]
        for call in business_works.create_case.await_args_list
    ]
    assert case_keys == ["batch-1:case:1", "batch-1:case:2"]
