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
        timeout_seconds: float = 300,
        max_output_tokens: int = 8192,
    ) -> None:
        self._gateway_url = gateway_url.rstrip("/")
        self._tokens = tokens
        self._allowed_models = allowed_models
        self._workload_tls = workload_tls or WorkloadTls()
        self._timeout_seconds = timeout_seconds
        self._max_output_tokens = max_output_tokens

    def resolve(self, reference: str, context: Mapping[str, Any]) -> OpenAIChat:
        logical_model = reference.rsplit("@", 1)[0]
        if logical_model not in self._allowed_models:
            raise ValueError(f"model reference is not configured: {reference}")
        run = context["run"]
        token = self._tokens.issue(
            tenant_id=str(run["tenantId"]),
            project_id=str(run["projectId"]),
            run_id=str(run["runId"]),
            task_execution_id=str(context["taskExecutionId"]),
            subject_id=f"agent-worker:{context['agentInstanceId']}",
            logical_model=logical_model,
        )
        return OpenAIChat(
            id=logical_model,
            api_key=token,
            base_url=f"{self._gateway_url}/v1",
            max_tokens=self._max_output_tokens,
            max_retries=0,
            http_client=httpx.AsyncClient(
                timeout=self._timeout_seconds,
                verify=self._workload_tls.client_context() or True,
            ),
        )
