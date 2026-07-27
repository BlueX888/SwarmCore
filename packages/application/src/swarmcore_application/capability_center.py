from __future__ import annotations

from copy import deepcopy
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from swarmcore_domain import (
    CapabilityKind,
    CapabilityReadinessStatus,
    CapabilitySummary,
)
from swarmcore_registry import AgentRegistration, RegistrySnapshot
from swarmcore_spec.models import AgentSpec

from .capability_readiness import CapabilityReadinessService
from .configurations import ConfigurationKind, ProjectConfigurationService
from .project_models import (
    is_runtime_provider_name,
    project_model_capability_summary,
    project_model_logical_id,
)
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
        configurations: ProjectConfigurationService | None = None,
    ) -> None:
        self._registry = registry
        self._readiness = readiness
        self._runs = runs or RunService()
        self._configurations = configurations or ProjectConfigurationService(registry)
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
        session: AsyncSession | None = None,
    ) -> tuple[CapabilitySummary, ...]:
        builtins = await self._readiness.project(
            tenant_id=tenant_id,
            project_id=project_id,
            environment=environment,
            registry=self._registry,
        )
        if session is None:
            return builtins
        try:
            agent_rows, _ = await self._configurations.list(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                kind=ConfigurationKind.AGENT,
                limit=1000,
            )
            model_rows, _ = await self._configurations.list(
                session,
                tenant_id=tenant_id,
                project_id=project_id,
                kind=ConfigurationKind.MODEL,
                limit=1000,
            )
        except Exception:
            return builtins
        project_models = self._project_model_summaries(model_rows)
        projection = (*builtins, *project_models)
        builtin_agents = {item.ref: item for item in builtins if item.kind is CapabilityKind.AGENT}
        project_agents: list[CapabilitySummary] = []
        for row in agent_rows:
            declaration = self._agent_declaration(row.configuration)
            if declaration is None:
                continue
            project_ref = self.project_agent_ref(row.id, row.revision)
            if declaration.ref is not None:
                target = builtin_agents.get(declaration.ref)
                if target is None:
                    continue
                project_agents.append(
                    target.model_copy(
                        update={
                            "ref": project_ref,
                            "name": row.name,
                            "description": f"基于系统智能体 {declaration.ref} 的项目配置。",
                            "source": "project",
                        }
                    )
                )
                continue
            registration = AgentRegistration(
                ref=project_ref,
                version=str(row.revision),
                role=declaration.role or row.name,
                description="项目自定义智能体。",
                instructions=declaration.instructions or "",
                model=declaration.model or "",
                tools=tuple(declaration.tools),
            )
            summary = await self._readiness.project_agent(
                tenant_id=tenant_id,
                project_id=project_id,
                environment=environment,
                registration=registration,
                registry=self._registry,
                projection=projection,
            )
            project_agents.append(
                summary.model_copy(update={"name": row.name, "source": "project"})
            )
        return (*project_agents, *project_models, *builtins)

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
        project_capability = capability_ref.startswith(
            "agent://project/"
        ) or capability_ref.startswith("model://project/")
        summaries = await self.list(
            tenant_id=tenant_id,
            project_id=project_id,
            environment=environment,
            session=session if project_capability else None,
        )
        summary = next((item for item in summaries if item.ref == capability_ref), None)
        if summary is None:
            raise LookupError("capability not found")
        if summary.readiness.status is not CapabilityReadinessStatus.READY:
            codes = ",".join(reason.code.value for reason in summary.readiness.reasons)
            raise ValueError(f"CAPABILITY_NOT_READY: {codes}")
        project_configuration = await self._resolve_project_agent(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            capability_ref=capability_ref,
        )
        raw_spec = (
            self.build_project_agent_spec(project_configuration.configuration, summary)
            if project_configuration is not None
            else self.build_spec(summary, input_data=input_data)
        )
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

    @staticmethod
    def project_agent_ref(configuration_id: UUID, revision: int) -> str:
        return f"agent://project/{configuration_id}@{revision}"

    @staticmethod
    def _project_model_summaries(rows: list[Any]) -> tuple[CapabilitySummary, ...]:
        summaries: list[CapabilitySummary] = []
        for row in rows:
            if not is_runtime_provider_name(row.name):
                continue
            logical = project_model_logical_id(str(row.source_ref))
            summary = project_model_capability_summary(
                logical_model=logical,
                revision=int(row.revision),
                configuration=row.configuration if isinstance(row.configuration, dict) else {},
            )
            if summary is not None:
                summaries.append(summary)
        return tuple(summaries)

    @staticmethod
    def _agent_declaration(configuration: dict[str, Any]) -> AgentSpec | None:
        spec = configuration.get("spec")
        if not isinstance(spec, dict):
            return None
        agents = spec.get("agents")
        graph = spec.get("graph")
        if not isinstance(agents, dict) or not isinstance(graph, dict):
            return None
        entrypoint = graph.get("entrypoint")
        nodes = graph.get("nodes")
        if not isinstance(entrypoint, str) or not isinstance(nodes, dict):
            return None
        node = nodes.get(entrypoint)
        if not isinstance(node, dict) or node.get("type") != "agent":
            return None
        agent_key = node.get("agent")
        declaration = agents.get(agent_key) if isinstance(agent_key, str) else None
        if not isinstance(declaration, dict):
            return None
        try:
            return AgentSpec.model_validate(declaration)
        except ValueError:
            return None

    async def _resolve_project_agent(
        self,
        session: AsyncSession,
        *,
        tenant_id: UUID,
        project_id: UUID,
        capability_ref: str,
    ) -> Any | None:
        prefix = "agent://project/"
        if not capability_ref.startswith(prefix) or "@" not in capability_ref:
            return None
        identity, revision_text = capability_ref[len(prefix) :].rsplit("@", 1)
        try:
            configuration_id = UUID(identity)
            revision = int(revision_text)
        except ValueError:
            return None
        row = await self._configurations.get(
            session,
            tenant_id=tenant_id,
            project_id=project_id,
            kind=ConfigurationKind.AGENT,
            configuration_id=configuration_id,
        )
        return row if row is not None and row.revision == revision else None

    @staticmethod
    def build_project_agent_spec(
        configuration: dict[str, Any], summary: CapabilitySummary
    ) -> dict[str, Any]:
        spec = deepcopy(configuration["spec"])
        graph = spec["graph"]
        entrypoint = graph["entrypoint"]
        spec.setdefault("inputSchema", summary.input_schema or {"type": "object"})
        spec.setdefault(
            "outputSchema",
            {
                "type": "object",
                "required": ["result"],
                "properties": {"result": summary.output_schema or {}},
                "additionalProperties": False,
            },
        )
        graph.setdefault("output", {"result": f"{{{{ tasks.{entrypoint}.output }}}}"})
        return {
            "apiVersion": "swarmcore.io/v1",
            "kind": "SwarmStrategy",
            "metadata": {"name": f"project-agent-{entrypoint}"},
            "spec": spec,
        }

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
                "input": {key: f"{{{{ input.{key} }}}}" for key in sorted(input_data)},
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
