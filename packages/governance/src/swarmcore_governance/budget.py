from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4

from .policy import PolicyEngine, PolicyRequest


class BudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class ModelCapability:
    tenant_id: str
    project_id: str
    run_id: str
    task_execution_id: str
    subject_id: str
    logical_model: str
    expires_at: int
    jti: str


class ModelCapabilityIssuer:
    def __init__(self, secret: bytes) -> None:
        if len(secret) < 32:
            raise ValueError("model capability secret must contain at least 32 bytes")
        self._secret = secret

    def issue(
        self,
        *,
        tenant_id: str,
        project_id: str,
        run_id: str,
        task_execution_id: str,
        subject_id: str,
        logical_model: str,
        ttl_seconds: int = 300,
    ) -> str:
        payload = {
            "tenantId": tenant_id,
            "projectId": project_id,
            "runId": run_id,
            "taskExecutionId": task_execution_id,
            "subjectId": subject_id,
            "logicalModel": logical_model,
            "exp": int(time.time()) + min(ttl_seconds, 300),
            "jti": uuid4().hex,
        }
        encoded = _b64(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
        signature = _b64(hmac.new(self._secret, encoded.encode(), hashlib.sha256).digest())
        return f"{encoded}.{signature}"

    def verify(self, token: str) -> ModelCapability:
        try:
            encoded, signature = token.split(".", 1)
            expected = _b64(
                hmac.new(self._secret, encoded.encode(), hashlib.sha256).digest()
            )
            if not hmac.compare_digest(signature, expected):
                raise ValueError("invalid model capability")
            payload = json.loads(_decode(encoded))
            capability = ModelCapability(
                tenant_id=str(payload["tenantId"]),
                project_id=str(payload["projectId"]),
                run_id=str(payload["runId"]),
                task_execution_id=str(payload["taskExecutionId"]),
                subject_id=str(payload["subjectId"]),
                logical_model=str(payload["logicalModel"]),
                expires_at=int(payload["exp"]),
                jti=str(payload["jti"]),
            )
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid model capability") from exc
        if capability.expires_at <= int(time.time()):
            raise ValueError("model capability expired")
        return capability


@dataclass(frozen=True)
class BudgetLimits:
    max_tokens: int
    max_cost_usd: float
    on_exhausted: str = "fail"

    def __post_init__(self) -> None:
        if self.max_tokens < 1 or self.max_cost_usd <= 0:
            raise ValueError("budget limits must be positive")
        if self.on_exhausted not in {"fail", "partial_result", "wait_for_budget_approval"}:
            raise ValueError("unsupported budget exhaustion behavior")


@dataclass(frozen=True)
class ModelUsage:
    input_tokens: int
    output_tokens: int
    cost_usd: float
    model: str
    provider: str
    price_version: str

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class ModelResponse:
    content: str
    usage: ModelUsage


class ModelAdapter(Protocol):
    async def invoke(
        self, *, model: str, messages: list[dict[str, str]], max_tokens: int
    ) -> ModelResponse: ...


@dataclass
class _Ledger:
    limits: BudgetLimits
    used_tokens: int = 0
    used_cost_usd: float = 0.0
    reserved_tokens: int = 0
    warned: bool = False


class BudgetManager:
    def __init__(self) -> None:
        self._ledgers: dict[str, _Ledger] = {}
        self._lock = asyncio.Lock()

    async def create(self, run_id: str, limits: BudgetLimits) -> None:
        async with self._lock:
            existing = self._ledgers.get(run_id)
            if existing is not None and existing.limits != limits:
                raise ValueError("run budget is immutable")
            self._ledgers.setdefault(run_id, _Ledger(limits))

    async def reserve(self, run_id: str, max_tokens: int) -> None:
        async with self._lock:
            ledger = self._ledgers[run_id]
            if ledger.used_tokens + ledger.reserved_tokens + max_tokens > ledger.limits.max_tokens:
                raise BudgetExceeded(ledger.limits.on_exhausted)
            ledger.reserved_tokens += max_tokens

    async def commit(self, run_id: str, reserved_tokens: int, usage: ModelUsage) -> str | None:
        async with self._lock:
            ledger = self._ledgers[run_id]
            ledger.reserved_tokens = max(0, ledger.reserved_tokens - reserved_tokens)
            ledger.used_tokens += usage.total_tokens
            ledger.used_cost_usd += usage.cost_usd
            ratio = max(
                ledger.used_tokens / ledger.limits.max_tokens,
                ledger.used_cost_usd / ledger.limits.max_cost_usd,
            )
            if ratio >= 1:
                return "budget.exhausted"
            if ratio >= 0.8 and not ledger.warned:
                ledger.warned = True
                return "budget.warning"
            return None

    async def release(self, run_id: str, reserved_tokens: int) -> None:
        async with self._lock:
            ledger = self._ledgers[run_id]
            ledger.reserved_tokens = max(0, ledger.reserved_tokens - reserved_tokens)

    def snapshot(self, run_id: str) -> dict[str, Any]:
        ledger = self._ledgers[run_id]
        return {
            "tokens": ledger.used_tokens,
            "costUsd": round(ledger.used_cost_usd, 8),
            "reservedTokens": ledger.reserved_tokens,
            "maxTokens": ledger.limits.max_tokens,
            "maxCostUsd": ledger.limits.max_cost_usd,
        }


class ModelGateway:
    def __init__(
        self,
        adapters: dict[str, ModelAdapter],
        routes: dict[str, tuple[str, str]],
        budgets: BudgetManager,
        policy: PolicyEngine,
    ) -> None:
        self._adapters = adapters
        self._routes = routes
        self._budgets = budgets
        self._policy = policy

    async def invoke(
        self,
        request: PolicyRequest,
        *,
        run_id: str,
        logical_model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
    ) -> tuple[ModelResponse, str | None]:
        (await self._policy.evaluate(request)).enforce()
        try:
            provider, model = self._routes[logical_model]
            adapter = self._adapters[provider]
        except KeyError as exc:
            raise ValueError("model route is not registered") from exc
        await self._budgets.reserve(run_id, max_tokens)
        try:
            response = await adapter.invoke(model=model, messages=messages, max_tokens=max_tokens)
        except Exception:
            await self._budgets.release(run_id, max_tokens)
            raise
        event = await self._budgets.commit(run_id, max_tokens, response.usage)
        if response.usage.provider != provider or response.usage.model != model:
            raise ValueError("model adapter returned usage outside the resolved route")
        return response, event


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
