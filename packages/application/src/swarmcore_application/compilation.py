from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from swarmcore_compiler import CompileError
from swarmcore_registry import builtin_registry

from .services import StrategyService


class CompilationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    valid: bool
    normalized_spec: dict[str, Any] | None = Field(default=None, alias="normalizedSpec")
    plan: dict[str, Any] | None = None
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)


class CompilationService:
    def __init__(self, strategies: StrategyService | None = None) -> None:
        self._strategies = strategies or StrategyService()

    def compile(
        self,
        raw_spec: dict[str, Any],
        *,
        registry_snapshot: str = builtin_registry().snapshot_id,
        policy_revision: str = "m3",
    ) -> CompilationResult:
        try:
            spec, plan = self._strategies.compile(
                raw_spec,
                registry_snapshot=registry_snapshot,
                policy_revision=policy_revision,
            )
            return CompilationResult(
                valid=True,
                normalizedSpec=spec.model_dump(mode="json", by_alias=True, exclude_none=True),
                plan=plan.model_dump(mode="json", by_alias=True),
            )
        except CompileError as exc:
            return CompilationResult(
                valid=False,
                diagnostics=[item.model_dump(mode="json") for item in exc.diagnostics],
            )
        except ValidationError as exc:
            return CompilationResult(
                valid=False,
                diagnostics=[
                    {
                        "severity": "error",
                        "code": "STRUCTURAL_VALIDATION_ERROR",
                        "path": "$." + ".".join(str(part) for part in item["loc"]),
                        "message": item["msg"],
                    }
                    for item in exc.errors(include_url=False)
                ],
            )

    def validate(self, raw_spec: dict[str, Any]) -> CompilationResult:
        return self.compile(raw_spec).model_copy(update={"plan": None})
