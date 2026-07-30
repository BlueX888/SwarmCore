from datetime import UTC, datetime
from uuid import uuid4

from swarmcore_persistence import OutboxClaim, claim_outbox, owns_outbox_claim
from swarmcore_persistence.models import OutboxEvent


def test_outbox_fencing_rejects_stale_generation() -> None:
    event = OutboxEvent(
        id=uuid4(),
        tenant_id=uuid4(),
        aggregate_id=uuid4(),
        destination="nats",
        partition_key="run",
        source_id=uuid4(),
        type="run.started",
        payload={},
        lock_generation=0,
    )
    claim = claim_outbox(event, worker_id="worker-a", now=datetime.now(UTC))

    assert owns_outbox_claim(event, claim, worker_id="worker-a")
    assert not owns_outbox_claim(
        event,
        OutboxClaim(id=event.id, generation=claim.generation - 1),
        worker_id="worker-a",
    )
    assert not owns_outbox_claim(event, claim, worker_id="worker-b")
