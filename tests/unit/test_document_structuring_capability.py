from __future__ import annotations

from pathlib import Path
from uuid import UUID

from jsonschema import Draft202012Validator
from swarmcore_application import StrategyService
from swarmcore_application.capability_tool_executors import (
    _document_artifact_object_key,
)
from swarmcore_application.document_structuring import (
    apply_human_review,
    document_package_artifacts,
    finalize_document_structuring,
    prepare_document_structuring,
)
from swarmcore_capability_document_structuring import (
    MANIFEST,
    MODELS,
    REFERENCES,
    SCHEMAS,
    STRATEGIES,
)
from swarmcore_persistence.models import Base
from swarmcore_registry import CapabilityPackManifest, builtin_registry
from swarmcore_spec import SwarmStrategy


def test_document_structuring_capability_assets_compile() -> None:
    manifest = CapabilityPackManifest.model_validate(MANIFEST)
    strategy = SwarmStrategy.model_validate(
        STRATEGIES["strategy://document-structuring/execute@1"]
    )
    registry = builtin_registry()

    assert manifest.metadata.name == "document-structuring"
    assert strategy.spec.budget.max_agents == 1
    assert set(manifest.spec.agents) <= REFERENCES
    assert set(manifest.spec.tools) <= REFERENCES
    assert all(registry.resolve_agent(ref) is not None for ref in manifest.spec.agents)
    assert all(registry.resolve_model(ref) is not None for ref in MODELS)
    assert all(registry.resolve_tool(ref) is not None for ref in manifest.spec.tools)
    _, plan = StrategyService().compile(
        STRATEGIES[manifest.spec.strategies.execute],
        registry_snapshot=registry.snapshot_id,
        policy_revision="test",
    )
    assert set(plan.resolved_tools) == set(manifest.spec.tools)
    assert {
        str(value["registryRef"])
        for value in plan.resolved_agents.values()
        if value.get("registryRef")
    } == set(manifest.spec.agents)
    for schema in SCHEMAS.values():
        Draft202012Validator.check_schema(schema)
    structurer = registry.resolve_agent("agent://document/structurer@1")
    assert structurer is not None
    assert "never the JSON Schema itself" in structurer.instructions
    document_schema = structurer.output_schema["properties"]["documents"]["items"]
    assert "organization" not in document_schema["required"]
    Draft202012Validator(structurer.output_schema).validate(
        structurer.output_schema_fallback
    )
    assert structurer.output_schema_fallback["reviewRequired"] is True


def test_document_processing_events_have_migration_and_tenant_scope() -> None:
    table = Base.metadata.tables["document_processing_events"]
    assert {
        "tenant_id",
        "project_id",
        "processing_run_id",
        "event_seq",
    } <= set(table.columns.keys())
    migration = Path(
        "packages/persistence/alembic/versions/0020_document_processing_events.py"
    ).read_text(encoding="utf-8")
    assert 'revision: str = "0020_doc_processing_events"' in migration
    assert 'down_revision: str | None = "0019_procurement_supplier_risk"' in migration
    assert "ENABLE ROW LEVEL SECURITY" in migration
    assert "NULLIF(current_setting('app.tenant_id'" in migration


def test_document_artifact_object_key_avoids_nested_windows_paths() -> None:
    key = _document_artifact_object_key(
        tenant_id=UUID("1813c340-7bdc-42ed-b12d-cb9c91bf1fb3"),
        project_id=UUID("38c74291-3e6b-4fbe-822a-964d5ee43b1a"),
        run_id=UUID("019fa711-c272-75e1-8a18-783c5ce315a7"),
        artifact_id=UUID("019fa714-1f6e-7d3f-892f-a936ef41a980"),
        filename=(
            "tables/019fa704-bd47-7def-970f-a92796a1a20c-table-1.csv"
        ),
    )

    assert key.endswith("/019fa714-1f6e-7d3f-892f-a936ef41a980.csv")
    assert "/tables/" not in key
    assert len(key) < 200


def test_finalize_requires_evidence_and_human_review_can_correct() -> None:
    prepared = prepare_document_structuring(
        [
            {
                "documentId": "doc-1",
                "documentVersionId": "version-1",
                "filename": "contract.odt",
                "mediaType": "application/vnd.oasis.opendocument.text",
                "sha256": "a" * 64,
                "data": {
                    "status": "READY",
                    "documentType": {
                        "label": "CONTRACT",
                        "confidence": 0.99,
                        "evidence": [{"page": 1, "excerpt": "Contract"}],
                    },
                    "content": {"chunks": [], "tables": [], "sections": []},
                    "extractions": [],
                },
            }
        ]
    )
    package = finalize_document_structuring(
        prepared,
        {
            "schemaVersion": "schema://document-structuring/agent-result@1",
            "summary": "已提取合同。",
            "qualityFlags": [],
            "reviewRequired": True,
            "documents": [
                {
                    "documentVersionId": "version-1",
                    "classification": {
                        "label": "CONTRACT",
                        "confidence": 0.99,
                        "evidence": [{"page": 1, "excerpt": "Contract"}],
                    },
                    "fields": [
                        {
                            "fieldPath": "contract.reference",
                            "machineValue": "Click here to enter reference",
                            "confidence": 0.99,
                            "reviewStatus": "PENDING",
                            "evidenceRefs": [],
                        }
                    ],
                    "organization": {},
                    "qualityFlags": [],
                }
            ],
        },
    )

    assert package["reviewRequired"] is True
    assert package["documents"][0]["fields"][0]["machineValue"] is None
    corrected = apply_human_review(
        package,
        {
            "decision": "CORRECT",
            "reason": "对照原件确认",
            "fieldCorrections": [
                {
                    "documentVersionId": "version-1",
                    "fieldPath": "contract.reference",
                    "value": "RM6268",
                }
            ],
        },
    )
    assert corrected["status"] == "READY"
    assert corrected["reviewRequired"] is False
    assert corrected["documents"][0]["fields"][0]["effectiveValue"] == "RM6268"
    assert {
        "structured-document.json",
        "content.md",
        "evidence-manifest.json",
        "review-log.json",
    } <= document_package_artifacts(corrected).keys()
