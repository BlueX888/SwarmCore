from __future__ import annotations

from typing import Any

from swarmcore_domain import (
    CapabilityKind,
    CapabilityReadiness,
    CapabilitySummary,
    ReadinessReason,
    ReadinessReasonCode,
)
from swarmcore_registry.project_models import (
    is_project_model_ref,
    is_runtime_provider_name,
    parse_project_model_id,
    project_model_logical_id,
    runtime_provider_name,
    synthesize_project_model_registration,
)

__all__ = [
    "is_project_model_ref",
    "is_runtime_provider_name",
    "parse_project_model_id",
    "project_model_capability_summary",
    "project_model_logical_id",
    "runtime_provider_name",
    "synthesize_project_model_registration",
]


def project_model_capability_summary(
    *,
    logical_model: str,
    revision: int,
    configuration: dict[str, Any],
) -> CapabilitySummary | None:
    if parse_project_model_id(logical_model) is None:
        return None
    provider_url = str(configuration.get("providerUrl", "")).strip()
    model_name = str(configuration.get("modelName", "")).strip()
    secret_ref = str(configuration.get("secretRef", "")).strip()
    display_name = str(configuration.get("displayName", "")).strip() or model_name or "项目模型"
    reasons: list[ReadinessReason] = []
    if not provider_url or not model_name:
        reasons.append(
            ReadinessReason(
                code=ReadinessReasonCode.MODEL_ROUTE_MISSING,
                message="No provider route is configured.",
            )
        )
    if not secret_ref:
        reasons.append(
            ReadinessReason(
                code=ReadinessReasonCode.SECRET_MISSING,
                message="The provider credential cannot be leased.",
            )
        )
    readiness = (
        CapabilityReadiness.not_ready(*reasons) if reasons else CapabilityReadiness.ready()
    )
    return CapabilitySummary(
        ref=f"{project_model_logical_id(logical_model)}@{revision}",
        kind=CapabilityKind.MODEL,
        name=display_name,
        description=f"项目模型配置 · {model_name}" if model_name else "项目模型配置",
        source="project",
        readiness=readiness,
        inputSchema={"type": "object"},
        outputSchema={"type": "object"},
    )
