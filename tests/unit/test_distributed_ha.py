from pathlib import Path

import pytest
from sqlalchemy.dialects import postgresql
from swarmcore_event_publisher.main import Settings as EventPublisherSettings
from swarmcore_projection_reconciler.main import reconcile_candidates_query
from swarmcore_worker_agent.main import Settings as AgentWorkerSettings
from swarmcore_worker_control.main import Settings as ControlWorkerSettings
from swarmcore_worker_tool.main import Settings as ToolWorkerSettings


def test_reconciler_claims_distinct_batches_across_replicas() -> None:
    sql = str(
        reconcile_candidates_query(25).compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    ).upper()
    assert "RECONCILED_AT" in sql
    assert "FOR UPDATE SKIP LOCKED" in sql
    assert "LIMIT 25" in sql


def test_worker_capacity_and_stream_replication_are_explicit() -> None:
    assert AgentWorkerSettings(_env_file=None).worker_max_concurrent_activities == 32
    assert ToolWorkerSettings(_env_file=None).worker_max_concurrent_activities == 32
    control = ControlWorkerSettings(_env_file=None)
    assert control.worker_max_concurrent_workflows == 100
    assert control.worker_max_concurrent_activities == 16
    assert EventPublisherSettings(_env_file=None).nats_stream_replicas == 1


def test_production_control_worker_requires_shared_artifact_store() -> None:
    with pytest.raises(ValueError, match="shared S3"):
        ControlWorkerSettings(
            _env_file=None,
            deployment_mode="production",
            artifact_store="local",
            artifact_root=str(Path(".tmp/artifacts")),
        )
    configured = ControlWorkerSettings(
        _env_file=None,
        deployment_mode="production",
        artifact_store="s3",
        artifact_s3_bucket="swarmcore-artifacts",
    )
    assert configured.artifact_store == "s3"


def test_distributed_lease_migrations_form_single_head() -> None:
    fencing = Path(
        "packages/persistence/alembic/versions/0021_distributed_lease_fencing.py"
    ).read_text(encoding="utf-8")
    reconciler = Path(
        "packages/persistence/alembic/versions/0022_reconciler_claims.py"
    ).read_text(encoding="utf-8")
    assert 'down_revision: str | None = "0020_doc_processing_events"' in fencing
    assert '"lock_generation"' in fencing
    assert '"lease_generation"' in fencing
    assert 'down_revision: str | None = "0021_distributed_lease_fencing"' in reconciler
    assert '"reconciled_at"' in reconciler
