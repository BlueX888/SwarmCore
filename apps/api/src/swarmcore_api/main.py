from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from jsonschema import ValidationError as JsonSchemaValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from swarmcore_application import RunCommandConflictError, RunNotTerminalError
from swarmcore_compiler import CompileError
from swarmcore_governance import OpaPolicyEngine, PolicyDenied, PolicyError, RolePolicyEngine
from swarmcore_observability import (
    SwarmMetrics,
    configure_json_logging,
    configure_telemetry,
    get_tracer,
)
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
        app.state.policy = (
            OpaPolicyEngine(resolved.opa_decision_url)
            if resolved.policy_mode == "opa"
            else RolePolicyEngine()
        )
        yield
        await app.state.database.dispose()

    app = FastAPI(title="SwarmCore API", version="0.1.0", lifespan=lifespan)
    app.state.metrics = SwarmMetrics.create("api")
    app.state.settings = resolved
    app.state.policy = (
        OpaPolicyEngine(resolved.opa_decision_url)
        if resolved.policy_mode == "opa"
        else RolePolicyEngine()
    )
    if resolved.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved.cors_origins),
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "Idempotency-Key",
                "Last-Event-ID",
                "Mcp-Protocol-Version",
            ],
        )
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
        ) as span:
            response = await call_next(request)
            for state_name, attribute in (
                ("tenant_id", "tenant.id"),
                ("project_id", "project.id"),
                ("run_id", "swarm.run.id"),
            ):
                value = getattr(request.state, state_name, None)
                if value is not None:
                    span.set_attribute(attribute, str(value))
            span.set_attribute("http.response.status_code", response.status_code)
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
            )
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.exception_handler(LookupError)
    async def not_found(request: Request, exc: LookupError) -> JSONResponse:
        return _problem(request, 404, "NOT_FOUND", str(exc))

    @app.exception_handler(PersistenceConflictError)
    async def conflict(request: Request, exc: PersistenceConflictError) -> JSONResponse:
        return _problem(request, 409, "CONFLICT", str(exc))

    @app.exception_handler(RunCommandConflictError)
    async def command_conflict(request: Request, exc: RunCommandConflictError) -> JSONResponse:
        return _problem(request, 409, "CONFLICT", str(exc))

    @app.exception_handler(RunNotTerminalError)
    async def run_not_terminal(request: Request, exc: RunNotTerminalError) -> JSONResponse:
        return _problem(request, 409, "RUN_NOT_TERMINAL", str(exc))

    @app.exception_handler(CompileError)
    async def compile_error(request: Request, exc: CompileError) -> JSONResponse:
        return _problem(request, 422, "SPEC_INVALID", str(exc))

    @app.exception_handler(ValidationError)
    async def validation_error(request: Request, exc: ValidationError) -> JSONResponse:
        return _problem(request, 422, "VALIDATION_ERROR", str(exc))

    @app.exception_handler(JsonSchemaValidationError)
    async def json_schema_validation_error(
        request: Request, exc: JsonSchemaValidationError
    ) -> JSONResponse:
        return _problem(request, 422, "INPUT_SCHEMA_INVALID", exc.message)

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

    @app.exception_handler(PolicyError)
    async def policy_error(request: Request, exc: PolicyError) -> JSONResponse:
        return _problem(request, 503, "POLICY_UNAVAILABLE", str(exc))

    @app.exception_handler(PolicyDenied)
    async def policy_denied(request: Request, exc: PolicyDenied) -> JSONResponse:
        return _problem(request, 403, "POLICY_DENIED", str(exc))

    return app


def _problem(request: Request, status: int, code: str, detail: str) -> JSONResponse:
    problem = Problem(title=code.replace("_", " ").title(), status=status, code=code, detail=detail)
    return JSONResponse(
        problem.model_dump(mode="json", by_alias=True),
        status_code=status,
        media_type="application/problem+json",
    )


def run() -> None:
    configure_json_logging()
    settings = Settings()
    telemetry = configure_telemetry(
        "api", endpoint=settings.otlp_endpoint, enabled=settings.telemetry_enabled
    )
    try:
        uvicorn.run("swarmcore_api.main:create_app", factory=True, host="0.0.0.0", port=8000)
    finally:
        telemetry.shutdown()
