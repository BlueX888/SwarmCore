from swarmcore_application.workbench import WorkbenchService
from swarmcore_capability_contract_post_evaluation import SCHEMAS


def test_schema_requires_non_empty_documents_for_post_evaluation_input() -> None:
    service = WorkbenchService(capability_packs=None, schemas=dict(SCHEMAS))  # type: ignore[arg-type]
    assert service._schema_requires_non_empty(
        "schema://contract/post-evaluation-input@2", "documents"
    )
    assert service._schema_requires_non_empty(
        "schema://contract/post-evaluation-input@2", "subjects"
    )
    assert not service._schema_requires_non_empty(
        "schema://contract/post-evaluation-input@2", "attachments"
    )
    assert not service._schema_requires_non_empty("schema://missing", "documents")


def test_selection_provenance_is_frozen_for_invoice_and_deviation_runs() -> None:
    assert WorkbenchService._requires_selection_provenance("invoice-assurance")
    assert WorkbenchService._requires_selection_provenance("deviation-analysis")
    assert not WorkbenchService._requires_selection_provenance("contract-integrity")
