from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class AuditRecord:
    tenant_id: str
    project_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    outcome: str
    policy_revision: str | None = None
    run_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AuditWriter(Protocol):
    async def append(self, record: AuditRecord) -> None: ...


class InMemoryAuditWriter:
    def __init__(self) -> None:
        self._records: list[AuditRecord] = []
        self._lock = asyncio.Lock()

    async def append(self, record: AuditRecord) -> None:
        async with self._lock:
            self._records.append(record)

    def export(self, *, tenant_id: str, project_id: str) -> tuple[AuditRecord, ...]:
        return tuple(
            record
            for record in self._records
            if record.tenant_id == tenant_id and record.project_id == project_id
        )
