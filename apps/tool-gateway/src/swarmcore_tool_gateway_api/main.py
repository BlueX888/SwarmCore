from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from pydantic_settings import BaseSettings, SettingsConfigDict
from swarmcore_domain import uuid7
from swarmcore_persistence import (
    Database,
    EventRepository,
    PostgresEffectJournal,
    tenant_transaction,
)
from swarmcore_registry import builtin_registry
from swarmcore_tool_gateway import (
    AuditEvent,
    CapabilityTokenIssuer,
    EffectConflict,
    EffectInProgress,
    GatewayError,
    ToolGateway,
    ToolInvocation,
    builtin_executors,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SWARMCORE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://swarmcore:swarmcore@localhost:5433/swarmcore"
    tool_capability_secret: str = "development-only-capability-secret-32-bytes"
    tool_gateway_host: str = "127.0.0.1"
    tool_gateway_port: int = 8090


class PostgresToolAuditSink:
    def __init__(self, database: Database) -> None:
        self._database = database
        self._events = EventRepository()

    async def record(self, event: AuditEvent) -> None:
        tenant_id = UUID(event.tenant_id)
        project_id = UUID(event.project_id)
        async with tenant_transaction(
            self._database.sessions, tenant_id=tenant_id, project_id=project_id
        ) as session:
            await self._events.append(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                run_id=UUID(event.run_id),
                transition_id=uuid7(),
                event_type=event.type,
                payload={
                    "nodeKey": event.node_key,
                    "toolRef": event.tool_ref,
                    "effectId": event.effect_id,
                    **event.data,
                },
                occurred_at=datetime.now(UTC),
            )


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database = Database(configured.database_url)
        app.state.database = database
        app.state.gateway = ToolGateway(
            builtin_registry(),
            CapabilityTokenIssuer(configured.tool_capability_secret),
            PostgresEffectJournal(database.sessions),
            builtin_executors(),
            PostgresToolAuditSink(database),
        )
        try:
            yield
        finally:
            await database.dispose()

    app = FastAPI(title="SwarmCore Tool Gateway", lifespan=lifespan)

    @app.post("/internal/v1/tools/invoke")
    async def invoke(body: ToolInvocation, request: Request) -> dict[str, Any]:
        gateway: ToolGateway = request.app.state.gateway
        try:
            return await gateway.invoke(body)
        except EffectInProgress as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except EffectConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except GatewayError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.get("/healthz")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


def run() -> None:
    settings = Settings()
    uvicorn.run(
        create_app(settings), host=settings.tool_gateway_host, port=settings.tool_gateway_port
    )
