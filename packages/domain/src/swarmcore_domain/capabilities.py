from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CapabilityKind(StrEnum):
    AGENT = "agent"
    TOOL = "tool"
    MODEL = "model"
    POLICY = "policy"


class CapabilityReadinessStatus(StrEnum):
    READY = "READY"
    NOT_READY = "NOT_READY"


class ReadinessReasonCode(StrEnum):
    EXECUTOR_MISSING = "EXECUTOR_MISSING"
    ADAPTER_MISSING = "ADAPTER_MISSING"
    MODEL_ROUTE_MISSING = "MODEL_ROUTE_MISSING"
    SECRET_MISSING = "SECRET_MISSING"
    DEPENDENCY_NOT_READY = "DEPENDENCY_NOT_READY"
    DEPENDENCY_CYCLE = "DEPENDENCY_CYCLE"
    HEALTH_CHECK_FAILED = "HEALTH_CHECK_FAILED"
    ENVIRONMENT_NOT_ALLOWED = "ENVIRONMENT_NOT_ALLOWED"
    CAPABILITY_PACK_DISABLED = "CAPABILITY_PACK_DISABLED"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    POLICY_DENIED = "POLICY_DENIED"


class FrozenCapabilityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class ReadinessReason(FrozenCapabilityModel):
    code: ReadinessReasonCode
    message: str
    dependency_ref: str | None = Field(default=None, alias="dependencyRef")


class CapabilityReadiness(FrozenCapabilityModel):
    status: CapabilityReadinessStatus
    reasons: tuple[ReadinessReason, ...] = ()

    @classmethod
    def ready(cls) -> CapabilityReadiness:
        return cls(status=CapabilityReadinessStatus.READY)

    @classmethod
    def not_ready(cls, *reasons: ReadinessReason) -> CapabilityReadiness:
        if not reasons:
            raise ValueError("NOT_READY requires at least one reason")
        return cls(status=CapabilityReadinessStatus.NOT_READY, reasons=reasons)


class CapabilitySummary(FrozenCapabilityModel):
    ref: str
    kind: CapabilityKind
    name: str
    description: str
    source: str = "system"
    readiness: CapabilityReadiness
    risk: str | None = None
    input_schema: dict[str, Any] | None = Field(default=None, alias="inputSchema")
    output_schema: dict[str, Any] | None = Field(default=None, alias="outputSchema")
