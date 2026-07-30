from __future__ import annotations

import asyncio
from uuid import UUID

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Select, select
from swarmcore_observability import configure_json_logging, configure_telemetry
from swarmcore_persistence import Database, ProjectionReconciler
from swarmcore_persistence.models import Run


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    reconciler_database_url: str = (
        "postgresql+asyncpg://swarmcore_reconciler:swarmcore@localhost:5433/swarmcore"
    )
    reconciler_poll_seconds: float = 5.0
    reconciler_batch_size: int = 100
    otlp_endpoint: str = "http://localhost:4317"
    telemetry_enabled: bool = True


async def reconcile_once(database: Database, *, batch_size: int) -> int:
    """Repair a bounded batch using the dedicated BYPASSRLS reconciler role."""
    reconciler = ProjectionReconciler()
    async with database.sessions() as session, session.begin():
        run_ids = list(
            await session.scalars(reconcile_candidates_query(batch_size))
        )
        for run_id in run_ids:
            await reconciler.reconcile_run(session, run_id)
    return len(run_ids)


def reconcile_candidates_query(batch_size: int) -> Select[tuple[UUID]]:
    return (
        select(Run.id)
        .order_by(Run.reconciled_at.asc().nullsfirst(), Run.id)
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )


async def serve() -> None:
    settings = Settings()
    telemetry = configure_telemetry(
        "projection-reconciler",
        endpoint=settings.otlp_endpoint,
        enabled=settings.telemetry_enabled,
    )
    database = Database(settings.reconciler_database_url)
    try:
        while True:
            count = await reconcile_once(database, batch_size=settings.reconciler_batch_size)
            if count < settings.reconciler_batch_size:
                await asyncio.sleep(settings.reconciler_poll_seconds)
    finally:
        await database.dispose()
        telemetry.shutdown()


def run() -> None:
    configure_json_logging()
    asyncio.run(serve())
