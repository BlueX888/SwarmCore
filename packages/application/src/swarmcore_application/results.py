from __future__ import annotations

import json
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_persistence.models import Run, RunEvent, RunTask

_TERMINAL = {"SUCCEEDED", "FAILED", "CANCELLED", "TIMED_OUT", "REJECTED"}


class RunNotTerminalError(RuntimeError):
    pass


class ResultModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class ArtifactRef(ResultModel):
    artifact_id: UUID | None = Field(default=None, alias="artifactId")
    uri: str | None = None
    sha256: str | None = None
    mime_type: str | None = Field(default=None, alias="mimeType")


class TasksSummary(ResultModel):
    total: int
    succeeded: int
    failed: int
    skipped: int
    cancelled: int


class RunError(ResultModel):
    code: str
    message: str
    retryable: bool = False


class RunProvenance(ResultModel):
    strategy_version_id: UUID = Field(alias="strategyVersionId")
    plan_hash: str = Field(alias="planHash")
    runtime_version: str = Field(alias="runtimeVersion")
    policy_revision: str = Field(alias="policyRevision")


class RunResult(ResultModel):
    run_id: UUID = Field(alias="runId")
    status: str
    completion_quality: Literal["COMPLETE", "PARTIAL", "NONE"] = Field(
        alias="completionQuality"
    )
    output_schema_version: str = Field(default="result.v1", alias="outputSchemaVersion")
    output: dict[str, Any] | None
    artifacts: list[ArtifactRef]
    tasks_summary: TasksSummary = Field(alias="tasksSummary")
    usage: dict[str, float]
    warnings: list[str]
    unresolved_effects: list[dict[str, Any]] = Field(alias="unresolvedEffects")
    error: RunError | None
    provenance: RunProvenance


class RunResultService:
    async def get(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        run_id: UUID,
    ) -> RunResult:
        run = await session.scalar(
            select(Run).where(
                Run.id == run_id,
                Run.tenant_id == tenant_id,
                Run.project_id == project_id,
            )
        )
        if run is None:
            raise LookupError("run not found")
        if run.status not in _TERMINAL:
            raise RunNotTerminalError("run has not reached a terminal status")

        count_rows = (
            await session.execute(
                select(RunTask.status, func.count())
                .where(RunTask.run_id == run_id)
                .group_by(RunTask.status)
            )
        ).all()
        counts: dict[str, int] = {status: int(count) for status, count in count_rows}
        output, warnings = self._inline_output(run.output)
        succeeded = int(counts.get("SUCCEEDED", 0))
        error = await self._error(session, run)
        return RunResult(
            runId=run.id,
            status=run.status,
            completionQuality=(
                "COMPLETE" if run.status == "SUCCEEDED" else "PARTIAL" if succeeded else "NONE"
            ),
            output=output,
            artifacts=[ArtifactRef(uri=run.output_ref)] if run.output_ref else [],
            tasksSummary=TasksSummary(
                total=sum(counts.values()),
                succeeded=succeeded,
                failed=int(counts.get("FAILED", 0)),
                skipped=int(counts.get("SKIPPED", 0)),
                cancelled=int(counts.get("CANCELLED", 0)),
            ),
            usage=self._usage(run.usage),
            warnings=warnings,
            unresolvedEffects=[],
            error=error,
            provenance=RunProvenance(
                strategyVersionId=run.strategy_version_id,
                planHash=run.plan_hash,
                runtimeVersion=run.runtime_version,
                policyRevision=await self._policy_revision(session, run),
            ),
        )

    @staticmethod
    def _inline_output(output: dict[str, Any] | None) -> tuple[dict[str, Any] | None, list[str]]:
        if output is None:
            return None, []
        encoded = json.dumps(output, ensure_ascii=False, separators=(",", ":")).encode()
        if len(encoded) <= 256 * 1024:
            return output, []
        return None, ["OUTPUT_TOO_LARGE_FOR_INLINE_RESULT"]

    @staticmethod
    def _usage(usage: dict[str, Any]) -> dict[str, float]:
        aliases = {
            "input_tokens": "inputTokens",
            "output_tokens": "outputTokens",
            "cost_usd": "costUsd",
        }
        return {
            aliases.get(key, key): float(value)
            for key, value in usage.items()
            if isinstance(value, int | float) and not isinstance(value, bool)
        }

    @staticmethod
    async def _policy_revision(session: AsyncSession, run: Run) -> str:
        from swarmcore_persistence.models import StrategyVersion

        version = await session.get(StrategyVersion, run.strategy_version_id)
        if version is None:
            return "unknown"
        return str(version.plan.get("policy_revision", "unknown"))

    @staticmethod
    async def _error(session: AsyncSession, run: Run) -> RunError | None:
        if run.status == "SUCCEEDED":
            return None
        event = await session.scalar(
            select(RunEvent)
            .where(RunEvent.run_id == run.id, RunEvent.type == "run.failed")
            .order_by(RunEvent.event_seq.desc())
            .limit(1)
        )
        payload = event.payload if event else {}
        defaults = {
            "FAILED": "RUN_FAILED",
            "CANCELLED": "RUN_CANCELLED",
            "TIMED_OUT": "RUN_TIMED_OUT",
            "REJECTED": "RUN_REJECTED",
        }
        code = str(payload.get("code", defaults.get(run.status, "RUN_FAILED")))
        return RunError(
            code=code,
            message=str(payload.get("message", code.replace("_", " ").title())),
            retryable=bool(payload.get("retryable", False)),
        )
