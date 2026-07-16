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
