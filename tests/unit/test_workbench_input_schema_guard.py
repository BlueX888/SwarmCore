from unittest.mock import MagicMock
from uuid import uuid4

from swarmcore_application.workbench import WorkbenchService
from swarmcore_capability_contract_integrity import SCHEMAS as INTEGRITY_SCHEMAS
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
    assert WorkbenchService._requires_selection_provenance("document-structuring")
    assert WorkbenchService._requires_selection_provenance(
        "procurement-supplier-risk"
    )
    assert not WorkbenchService._requires_selection_provenance("contract-integrity")


def test_v2_contract_integrity_runtime_fields_follow_the_declared_schema() -> None:
    service = WorkbenchService(
        capability_packs=None, schemas={**SCHEMAS, **INTEGRITY_SCHEMAS}  # type: ignore[arg-type]
    )

    assert service._schema_has_property(
        "schema://contract/validation-input@2", "resources"
    )
    assert not service._schema_has_property(
        "schema://contract/validation-input@2", "documents"
    )


def test_document_library_item_is_available_to_integrity_rules_as_an_attachment() -> None:
    document = MagicMock(id=uuid4(), category="CONTRACT")
    version = MagicMock(
        filename="demo-contract.pdf",
        media_type="application/pdf",
        sha256="a" * 64,
        version=1,
    )
    blob = MagicMock(id=uuid4(), metadata_json={})

    payload = WorkbenchService._document_attachment_payload((document, version, blob))

    assert payload["documentType"] == "contract"
    assert payload["filename"] == "demo-contract.pdf"
    assert payload["readable"] is True
