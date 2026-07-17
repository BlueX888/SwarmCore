from __future__ import annotations

import asyncio
import socket
from contextlib import suppress
from datetime import timedelta

import nats
from nats.js.api import RetentionPolicy, StorageType, StreamConfig
from nats.js.errors import BadRequestError
from pydantic_settings import BaseSettings, SettingsConfigDict
from swarmcore_observability import (
    SwarmMetrics,
    configure_json_logging,
    configure_telemetry,
    get_tracer,
)
from swarmcore_persistence import Database

from .publisher import EventPublisher


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://swarmcore:swarmcore@localhost:5433/swarmcore"
    nats_url: str = "nats://localhost:4222"
    event_publisher_poll_seconds: float = 0.2
    otlp_endpoint: str = "http://localhost:4317"
    telemetry_enabled: bool = True


async def serve() -> None:
    settings = Settings()
    telemetry = configure_telemetry(
        "event-publisher", endpoint=settings.otlp_endpoint, enabled=settings.telemetry_enabled
    )
    database = Database(settings.database_url)
    connection = await nats.connect(settings.nats_url)
    jetstream = connection.jetstream()
    with suppress(BadRequestError):
        await jetstream.add_stream(
            config=StreamConfig(
                name="SWARM_EVENTS",
                subjects=["swarm.events.*.*"],
                retention=RetentionPolicy.LIMITS,
                storage=StorageType.FILE,
                max_age=timedelta(hours=24).total_seconds(),
                num_replicas=1,
            )
        )
    publisher = EventPublisher(
        database.sessions,
        jetstream,
        worker_id=socket.gethostname(),
        metrics=SwarmMetrics.create("event-publisher"),
    )
    try:
        while True:
            with get_tracer("event-publisher").start_as_current_span("publish-batch"):
                count = await publisher.run_once()
            if count == 0:
                await asyncio.sleep(settings.event_publisher_poll_seconds)
    finally:
        await connection.drain()
        await database.dispose()
        telemetry.shutdown()


def run() -> None:
    configure_json_logging()
    asyncio.run(serve())
