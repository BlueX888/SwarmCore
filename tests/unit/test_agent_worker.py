import pytest
from swarmcore_governance import ModelCapabilityIssuer
from swarmcore_worker_agent import StaticModelResolver
from swarmcore_worker_agent.model_gateway import GatewayModelResolver


def test_model_resolver_only_allows_registered_references() -> None:
    resolver = StaticModelResolver({"model://general": "openai:gpt-4o-mini"})
    assert resolver.resolve("model://general", {}) == "openai:gpt-4o-mini"
    with pytest.raises(ValueError, match="not configured"):
        resolver.resolve("model://unregistered", {})


def test_gateway_model_resolver_scopes_agno_to_run_and_logical_model() -> None:
    tokens = ModelCapabilityIssuer(b"m" * 32)
    resolver = GatewayModelResolver(
        "http://model-gateway:8093", tokens, frozenset({"model://general"})
    )
    model = resolver.resolve(
        "model://general@1",
        {
            "run": {
                "tenantId": "tenant-1",
                "projectId": "project-1",
                "runId": "run-1",
            },
            "agentInstanceId": "agent-1",
            "taskExecutionId": "task-1",
        },
    )
    capability = tokens.verify(str(model.api_key))
    assert capability.run_id == "run-1"
    assert capability.task_execution_id == "task-1"
    assert capability.logical_model == "model://general"
    assert model.id == "model://general"
    assert str(model.base_url) == "http://model-gateway:8093/v1"
