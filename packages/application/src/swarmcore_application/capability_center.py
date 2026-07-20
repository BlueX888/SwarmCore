from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_domain import (
    CapabilityKind,
    CapabilityReadinessStatus,
    CapabilitySummary,
)
from swarmcore_registry import RegistrySnapshot

from .capability_readiness import CapabilityReadinessService
from .services import RunService


class CapabilityPresetResolver(Protocol):
    async def resolve_input(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        preset_id: UUID,
        capability_ref: str,
    ) -> dict[str, Any]: ...


class CapabilityCenterService:
    def __init__(
        self,
        registry: RegistrySnapshot,
        readiness: CapabilityReadinessService,
        runs: RunService | None = None,
    ) -> None:
        self._registry = registry
        self._readiness = readiness
        self._runs = runs or RunService()
        self._presets: CapabilityPresetResolver | None = None

    def attach_preset_resolver(self, presets: CapabilityPresetResolver) -> None:
        self._presets = presets

    @property
    def registry_snapshot_id(self) -> str:
        return self._registry.snapshot_id

    async def list(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
    ) -> tuple[CapabilitySummary, ...]:
        return await self._readiness.project(
            tenant_id=tenant_id,
            project_id=project_id,
            environment=environment,
            registry=self._registry,
        )

    async def run(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        environment: str,
        capability_ref: str,
        input_data: dict[str, Any],
        preset_id: UUID | None,
        idempotency_key: str,
        initiated_by: str,
        submitted_scopes: tuple[str, ...],
        auth_context_hash: str,
    ) -> tuple[Any, Any]:
        if preset_id is not None:
            if self._presets is None:
                raise ValueError("preset service is unavailable")
            preset_input = await self._presets.resolve_input(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                preset_id=preset_id,
                capability_ref=capability_ref,
            )
            input_data = {**preset_input, **input_data}
        summaries = await self.list(
            tenant_id=tenant_id,
            project_id=project_id,
            environment=environment,
        )
        summary = next((item for item in summaries if item.ref == capability_ref), None)
        if summary is None:
            raise LookupError("capability not found")
        if summary.readiness.status is not CapabilityReadinessStatus.READY:
            codes = ",".join(reason.code.value for reason in summary.readiness.reasons)
            raise ValueError(f"CAPABILITY_NOT_READY: {codes}")
        raw_spec = self.build_spec(summary, input_data=input_data)
        return await self._runs.create_inline(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            raw_spec=raw_spec,
            input_data=input_data,
            idempotency_key=idempotency_key,
            registry_snapshot=self._registry.snapshot_id,
            initiated_by=initiated_by,
            submitted_scopes=submitted_scopes,
            auth_context_hash=auth_context_hash,
        )

    def build_spec(
        self, summary: CapabilitySummary, *, input_data: dict[str, Any]
    ) -> dict[str, Any]:
        safe_name = summary.ref.rsplit("/", 1)[-1].replace("@", "-").replace(".", "-")
        input_schema = summary.input_schema or {"type": "object"}
        capability_output = summary.output_schema or {"type": "object"}
        node: dict[str, Any]
        agents: dict[str, Any] = {}
        if summary.kind is CapabilityKind.TOOL:
            node = {
                "type": "tool",
                "tool": summary.ref,
                "input": {
                    key: f"{{{{ input.{key} }}}}"
                    for key in sorted(input_data)
                },
            }
        elif summary.kind is CapabilityKind.AGENT:
            agents = {"capability": {"ref": summary.ref}}
            node = {"type": "agent", "agent": "capability"}
        elif summary.kind is CapabilityKind.MODEL:
            agents = {
                "capability": {
                    "role": "capability-model-runner",
                    "instructions": "Process the supplied input and return the final result.",
                    "model": summary.ref,
                }
            }
            node = {"type": "agent", "agent": "capability"}
        else:
            raise ValueError(f"capability kind cannot run directly: {summary.kind.value}")
        return {
            "apiVersion": "swarmcore.io/v1",
            "kind": "SwarmStrategy",
            "metadata": {"name": f"capability-{safe_name}"},
            "spec": {
                "inputSchema": input_schema,
                "outputSchema": {
                    "type": "object",
                    "required": ["result"],
                    "properties": {"result": capability_output},
                    "additionalProperties": False,
                },
                "agents": agents,
                "graph": {
                    "entrypoint": "capability",
                    "nodes": {"capability": node},
                    "output": {"result": "{{ tasks.capability.output }}"},
                },
            },
        }
