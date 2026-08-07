from __future__ import annotations

from uuid import UUID

import pytest
from swarmcore_api.sse import SseConnectionLimiter


@pytest.mark.asyncio
async def test_sse_limiter_enforces_actor_and_releases_slot() -> None:
    limiter = SseConnectionLimiter(per_actor=1, per_project=2)
    tenant_id = UUID("00000000-0000-0000-0000-000000000001")
    project_id = UUID("00000000-0000-0000-0000-000000000002")

    assert await limiter.acquire(tenant_id=tenant_id, project_id=project_id, actor_id="actor-a")
    assert not await limiter.acquire(tenant_id=tenant_id, project_id=project_id, actor_id="actor-a")
    assert await limiter.acquire(tenant_id=tenant_id, project_id=project_id, actor_id="actor-b")
    assert not await limiter.acquire(tenant_id=tenant_id, project_id=project_id, actor_id="actor-c")

    await limiter.release(tenant_id=tenant_id, project_id=project_id, actor_id="actor-a")
    assert await limiter.acquire(tenant_id=tenant_id, project_id=project_id, actor_id="actor-a")
