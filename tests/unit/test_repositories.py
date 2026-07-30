from sqlalchemy.dialects import postgresql
from swarmcore_persistence.repositories import (
    canonical_hash,
    pending_nats_outbox_query,
    pending_outbox_query,
    pending_temporal_outbox_query,
)


def test_canonical_hash_ignores_mapping_order() -> None:
    assert canonical_hash({"a": 1, "b": 2}) == canonical_hash({"b": 2, "a": 1})


def test_outbox_claim_uses_skip_locked_and_destination() -> None:
    statement = pending_outbox_query("temporal", limit=10)
    sql = str(statement.compile(dialect=postgresql.dialect())).upper()
    assert "FOR UPDATE SKIP LOCKED" in sql
    assert "DESTINATION" in sql
    assert "LIMIT" in sql


def test_temporal_claim_excludes_unfinished_earlier_commands() -> None:
    sql = str(
        pending_temporal_outbox_query(limit=10).compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).upper()
    assert "NOT (EXISTS" in sql
    assert "COMMAND_SEQ" in sql
    assert "DOCUMENT.PROCESSING.CANCEL.REQUESTED" in sql
    assert "DOCUMENT-TEMPORAL" in sql
    assert "PARTITION_KEY" in sql
    assert "AVAILABLE_AT" in sql
    assert "STATUS NOT IN ('DELIVERED', 'DEAD')" in sql
    assert "FOR UPDATE OF OUTBOX_EVENTS SKIP LOCKED" in sql
    assert "DELIVERING" in sql
    assert "LOCKED_UNTIL" in sql


def test_nats_claim_excludes_unpublished_earlier_events() -> None:
    sql = str(
        pending_nats_outbox_query(limit=10).compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).upper()
    assert "NOT (EXISTS" in sql
    assert "EVENT_SEQ" in sql
    assert "DELIVERED_AT IS NULL" in sql
    assert "LEFT OUTER JOIN" in sql
    assert "PARTITION_KEY" in sql
    assert "DELIVERING" in sql
    assert "LOCKED_UNTIL" in sql
