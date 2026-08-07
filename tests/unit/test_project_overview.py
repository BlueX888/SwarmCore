from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

from swarmcore_application.business_works import BusinessWorkSummary
from swarmcore_application.project_overview import (
    ProjectOverviewService,
    business_work_index_by_item_type,
    calculate_document_readiness,
    calculate_ready_to_start,
    calculate_run_counts,
)


def test_run_counts_include_only_current_active_and_waiting_states() -> None:
    active, waiting = calculate_run_counts(
        {
            "RUNNING": 2,
            "WAITING_APPROVAL": 3,
            "WAITING_INPUT": 1,
            "PAUSED": 4,
            "FAILED": 99,
            "SUCCEEDED": 88,
        }
    )

    assert active == 6
    assert waiting == 8


def test_document_readiness_honors_min_count_and_ignores_optional_requirements() -> None:
    requirements = (
        {"key": "contracts", "category": "CONTRACT", "required": True, "minCount": 2},
        {"key": "invoice", "category": "INVOICE", "required": True, "minCount": 1},
        {"key": "optional", "category": "REPORT", "required": False, "minCount": 5},
    )

    required, satisfied, ready = calculate_document_readiness(
        requirements,
        {"CONTRACT": 4, "INVOICE": 0, "REPORT": 9},
    )

    assert required == 3
    assert satisfied == 2
    assert ready is False


def test_no_required_documents_is_ready() -> None:
    assert calculate_document_readiness((), {}) == (0, 0, True)


def test_available_documents_are_deduplicated_across_binding_aliases() -> None:
    document_id = uuid4()
    work = cast(
        BusinessWorkSummary,
        SimpleNamespace(
            work_key="invoice-assurance",
            pack_name="invoice-assurance",
            work_item_type="invoice-assurance-case",
        ),
    )
    categories = ProjectOverviewService._available_categories_for_work(
        work,
        {
            "invoice-assurance": {"INVOICE": {document_id}},
            "invoice-assurance-case": {"INVOICE": {document_id}},
        },
    )

    assert categories == {"INVOICE": 1}


def test_ambiguous_work_type_is_not_silently_mislabeled() -> None:
    report = cast(
        BusinessWorkSummary,
        SimpleNamespace(work_item_type="post-evaluation", work_key="report-generation"),
    )
    contract = cast(
        BusinessWorkSummary,
        SimpleNamespace(work_item_type="post-evaluation", work_key="contract-post-evaluation"),
    )

    index = business_work_index_by_item_type([report, contract])

    assert "post-evaluation" not in index


def test_runtime_and_document_readiness_are_independent_inputs() -> None:
    requirements = cast(
        tuple[dict[str, Any], ...],
        ({"category": "CONTRACT", "required": True, "minCount": 1},),
    )
    _, _, documents_ready = calculate_document_readiness(requirements, {"CONTRACT": 1})

    assert documents_ready is True
    assert calculate_ready_to_start("not_configured", documents_ready) is False
    assert calculate_ready_to_start("runnable", documents_ready) is True
