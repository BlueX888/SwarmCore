from __future__ import annotations

import os
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest_asyncio
from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment


@dataclass
class TemporalTestEnvironment:
    client: Client
    embedded: WorkflowEnvironment | None = None


@pytest_asyncio.fixture
async def temporal_environment() -> AsyncIterator[TemporalTestEnvironment]:
    address = os.getenv("SWARMCORE_TEST_TEMPORAL_ADDRESS")
    if address:
        client = await Client.connect(
            address,
            namespace=os.getenv("SWARMCORE_TEST_TEMPORAL_NAMESPACE", "default"),
        )
        yield TemporalTestEnvironment(client=client)
        return

    embedded = await WorkflowEnvironment.start_time_skipping()
    try:
        yield TemporalTestEnvironment(client=embedded.client, embedded=embedded)
    finally:
        await embedded.shutdown()
