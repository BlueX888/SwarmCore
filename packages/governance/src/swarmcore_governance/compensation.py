from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


class CompensationError(RuntimeError):
    pass


Compensator = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass(frozen=True)
class CompensationEntry:
    effect_id: str
    operation: str
    input: dict[str, Any]


@dataclass(frozen=True)
class CompensationResult:
    effect_id: str
    status: str
    error: str | None = None


class CompensationManager:
    """Executes compensations in reverse effect order with per-effect deduplication."""

    def __init__(self, handlers: dict[str, Compensator]) -> None:
        self._handlers = handlers
        self._completed: set[str] = set()

    async def compensate(self, entries: list[CompensationEntry]) -> tuple[CompensationResult, ...]:
        results: list[CompensationResult] = []
        for entry in reversed(entries):
            if entry.effect_id in self._completed:
                results.append(CompensationResult(entry.effect_id, "ALREADY_COMPENSATED"))
                continue
            handler = self._handlers.get(entry.operation)
            if handler is None:
                results.append(
                    CompensationResult(entry.effect_id, "MANUAL_RECOVERY_REQUIRED", "no handler")
                )
                continue
            try:
                await handler(entry.input)
            except Exception as exc:
                results.append(
                    CompensationResult(
                        entry.effect_id,
                        "COMPENSATION_FAILED",
                        f"{type(exc).__name__}: {exc}"[:1000],
                    )
                )
            else:
                self._completed.add(entry.effect_id)
                results.append(CompensationResult(entry.effect_id, "COMPENSATED"))
        return tuple(results)
