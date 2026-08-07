from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Hashable, MutableMapping
from typing import TypeVar
from uuid import UUID

_Key = TypeVar("_Key", bound=Hashable)


class SseConnectionLimiter:
    def __init__(self, *, per_actor: int, per_project: int) -> None:
        self._per_actor = per_actor
        self._per_project = per_project
        self._actor_counts: dict[tuple[UUID, UUID, str], int] = defaultdict(int)
        self._project_counts: dict[tuple[UUID, UUID], int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def acquire(self, *, tenant_id: UUID, project_id: UUID, actor_id: str) -> bool:
        actor_key = (tenant_id, project_id, actor_id)
        project_key = (tenant_id, project_id)
        async with self._lock:
            if (
                self._actor_counts[actor_key] >= self._per_actor
                or self._project_counts[project_key] >= self._per_project
            ):
                return False
            self._actor_counts[actor_key] += 1
            self._project_counts[project_key] += 1
            return True

    async def release(self, *, tenant_id: UUID, project_id: UUID, actor_id: str) -> None:
        actor_key = (tenant_id, project_id, actor_id)
        project_key = (tenant_id, project_id)
        async with self._lock:
            self._decrement(self._actor_counts, actor_key)
            self._decrement(self._project_counts, project_key)

    @staticmethod
    def _decrement(counts: MutableMapping[_Key, int], key: _Key) -> None:
        remaining = counts.get(key, 0) - 1
        if remaining > 0:
            counts[key] = remaining
        else:
            counts.pop(key, None)
