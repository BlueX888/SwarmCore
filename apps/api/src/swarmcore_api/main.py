from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint
from swarmcore_compiler import CompileError
from swarmcore_observability import configure_telemetry, get_tracer
from swarmcore_persistence import Database
from swarmcore_persistence.errors import PersistenceConflictError

from .mcp import router as mcp_router
from .routes import router
from .schemas import Problem
from .settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = resolved
        app.state.database = Database(resolved.database_url)
        yield
        await app.state.database.dispose()

    app = FastAPI(title="SwarmCore API", version="0.1.0", lifespan=lifespan)
    app.state.settings = resolved
    app.include_router(router)
    app.include_router(mcp_router)

    @app.middleware("http")
    async def trace_request(
        request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        tracer = get_tracer("api")
        with tracer.start_as_current_span(
            f"HTTP {request.method}",
            attributes={"http.request.method": request.method, "url.path": request.url.path},
        ):
            return await call_next(request)

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(LookupError)
    async def not_found(request: Request, exc: LookupError) -> JSONResponse:
        return _problem(request, 404, "NOT_FOUND", str(exc))

    @app.exception_handler(PersistenceConflictError)
    async def conflict(request: Request, exc: PersistenceConflictError) -> JSONResponse:
        return _problem(request, 409, "CONFLICT", str(exc))

    @app.exception_handler(CompileError)
    async def compile_error(request: Request, exc: CompileError) -> JSONResponse:
        return _problem(request, 422, "SPEC_INVALID", str(exc))

    @app.exception_handler(ValidationError)
    async def validation_error(request: Request, exc: ValidationError) -> JSONResponse:
        return _problem(request, 422, "VALIDATION_ERROR", str(exc))

    @app.exception_handler(RequestValidationError)
    async def request_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return _problem(request, 422, "VALIDATION_ERROR", str(exc))

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        codes = {404: "NOT_FOUND", 409: "CONFLICT", 410: "CURSOR_EXPIRED", 422: "VALIDATION_ERROR"}
        return _problem(
            request,
            exc.status_code,
            codes.get(exc.status_code, "HTTP_ERROR"),
            str(exc.detail),
        )

    @app.exception_handler(ValueError)
    async def value_error(request: Request, exc: ValueError) -> JSONResponse:
        detail = str(exc)
        if detail == "IDEMPOTENCY_KEY_REUSED":
            return _problem(request, 409, "IDEMPOTENCY_KEY_REUSED", detail)
        return _problem(request, 422, "VALIDATION_ERROR", detail)

    return app


def _problem(request: Request, status: int, code: str, detail: str) -> JSONResponse:
    problem = Problem(title=code.replace("_", " ").title(), status=status, code=code, detail=detail)
    return JSONResponse(
        problem.model_dump(mode="json", by_alias=True),
        status_code=status,
        media_type="application/problem+json",
    )


def run() -> None:
    settings = Settings()
    telemetry = configure_telemetry(
        "api", endpoint=settings.otlp_endpoint, enabled=settings.telemetry_enabled
    )
    try:
        uvicorn.run("swarmcore_api.main:create_app", factory=True, host="0.0.0.0", port=8000)
    finally:
        telemetry.shutdown()
