from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx
from swarmcore_governance import ModelCapabilityIssuer, WorkloadTls

from agno.models.openai import OpenAIChat


class GatewayModelResolver:
    """Build an Agno model client that can call only the scoped Model Gateway."""

    def __init__(
        self,
        gateway_url: str,
        tokens: ModelCapabilityIssuer,
        allowed_models: frozenset[str],
        workload_tls: WorkloadTls | None = None,
    ) -> None:
        self._gateway_url = gateway_url.rstrip("/")
        self._tokens = tokens
        self._allowed_models = allowed_models
        self._workload_tls = workload_tls or WorkloadTls()

    def resolve(self, reference: str, context: Mapping[str, Any]) -> OpenAIChat:
        if reference not in self._allowed_models:
            raise ValueError(f"model reference is not configured: {reference}")
        run = context["run"]
        token = self._tokens.issue(
            tenant_id=str(run["tenantId"]),
            project_id=str(run["projectId"]),
            run_id=str(run["runId"]),
            task_execution_id=str(context["taskExecutionId"]),
            subject_id=f"agent-worker:{context['agentInstanceId']}",
            logical_model=reference,
        )
        return OpenAIChat(
            id=reference,
            api_key=token,
            base_url=f"{self._gateway_url}/v1",
            http_client=httpx.AsyncClient(
                timeout=120,
                verify=self._workload_tls.client_context() or True,
            ),
        )
