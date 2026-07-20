from sqlalchemy import UniqueConstraint
from swarmcore_persistence.models import Base


def test_core_phase_one_tables_exist() -> None:
    expected = {
        "tenants",
        "projects",
        "strategies",
        "strategy_drafts",
        "strategy_versions",
        "runs",
        "run_tasks",
        "task_executions",
        "attempts",
        "run_events",
        "outbox_events",
        "run_commands",
        "idempotency_keys",
        "tool_effects",
    }
    assert expected <= set(Base.metadata.tables)


def test_business_workbench_tables_exist() -> None:
    expected = {
        "capability_packs",
        "capability_pack_versions",
        "project_capability_bindings",
        "work_items",
        "work_item_revisions",
        "blob_objects",
        "work_item_attachments",
        "rule_sets",
        "rule_set_drafts",
        "rule_set_versions",
        "evaluations",
        "findings",
        "finding_actions",
        "reports",
        "document_extractions",
    }
    assert expected <= set(Base.metadata.tables)


def test_business_idempotency_constraints_exist() -> None:
    expected = {
        "capability_pack_versions": {
            "uq_capability_pack_versions_version",
            "uq_capability_pack_versions_hash",
        },
        "work_item_revisions": {"uq_work_item_revisions_number"},
        "evaluations": {"uq_evaluations_idempotency"},
        "findings": {"uq_findings_rule_key"},
        "reports": {"uq_reports_evaluation_format"},
        "document_extractions": {
            "uq_document_extractions_cache_key",
            "uq_document_extractions_pipeline",
        },
    }
    for table_name, names in expected.items():
        actual = {
            constraint.name
            for constraint in Base.metadata.tables[table_name].constraints
            if isinstance(constraint, UniqueConstraint)
        }
        assert names <= actual


def test_ordering_and_idempotency_constraints_exist() -> None:
    expected = {
        "run_events": {"uq_run_events_sequence", "uq_run_events_transition"},
        "run_commands": {"uq_run_commands_request", "uq_run_commands_sequence"},
        "outbox_events": {"uq_outbox_destination_source"},
        "tool_effects": {"uq_tool_effect_scope"},
    }
    for table_name, names in expected.items():
        table = Base.metadata.tables[table_name]
        actual = {
            constraint.name
            for constraint in table.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        assert names <= actual
