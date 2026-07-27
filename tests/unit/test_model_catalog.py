from swarmcore_application import CapabilityCatalogService
from swarmcore_model_gateway.main import Settings as ModelGatewaySettings
from swarmcore_registry import builtin_registry
from swarmcore_worker_agent.main import Settings as AgentWorkerSettings

SUPPORTED_MODELS = {
    "model://deepseek-v4-flash": "DeepSeek-V4-Flash",
    "model://deepseek-v4-pro": "DeepSeek-V4-Pro",
    "model://kimi-k2.5": "kimi-k2.5",
    "model://kimi-k2.7-code": "kimi-k2.7-code",
}


def test_supported_models_are_available_and_routed_consistently() -> None:
    registry = builtin_registry()
    catalog_refs = {model.ref for model in CapabilityCatalogService().get().models}
    gateway_routes = ModelGatewaySettings(_env_file=None).model_routes
    worker_routes = AgentWorkerSettings(_env_file=None).models

    for logical_model, provider_model in SUPPORTED_MODELS.items():
        registration = registry.resolve_model(logical_model)
        assert registration is not None
        assert registration.provider_model == provider_model
        assert registration.ref in catalog_refs
        assert gateway_routes[logical_model] == provider_model
        assert worker_routes[logical_model] == provider_model


def test_registered_agent_definitions_are_available_for_safe_customization() -> None:
    catalog = CapabilityCatalogService().get()
    agents = {item.id: item for item in catalog.agents if item.id.startswith("agent://")}

    assert set(agents) == {
        "agent://builtin/researcher@1",
        "agent://contract/document-classifier@1",
        "agent://contract/field-extractor@1",
        "agent://contract/post-evaluation-analyst@1",
        "agent://contract/baseline-analyst@1",
        "agent://contract/baseline-analyst@2",
        "agent://contract/performance-quality-analyst@1",
        "agent://contract/performance-quality-analyst@2",
        "agent://contract/finance-invoice-analyst@1",
        "agent://contract/finance-invoice-analyst@2",
        "agent://contract/deviation-risk-analyst@1",
        "agent://contract/deviation-risk-analyst@2",
        "agent://contract/evidence-reviewer@1",
        "agent://contract/report-narrator@1",
        "agent://deviation/schedule-scope-fact-analyst@1",
        "agent://deviation/cost-change-fact-analyst@1",
        "agent://deviation/root-cause-analyst@1",
        "agent://deviation/responsibility-analyst@1",
        "agent://deviation/evidence-reviewer@1",
        "agent://deviation/report-narrator@1",
    }
    assert agents["agent://builtin/researcher@1"].model == "model://general@1"
    assert agents["agent://builtin/researcher@1"].tools == ["tool://search@1"]
    assert agents["agent://builtin/researcher@1"].input_schema["required"] == ["topic"]
    assert agents["agent://builtin/researcher@1"].input_schema["properties"][
        "maxSources"
    ]["default"] == 8
    for reference in (
        "agent://contract/document-classifier@1",
        "agent://contract/field-extractor@1",
    ):
        assert agents[reference].model == "model://general@1"
        assert agents[reference].tools == ["tool://document/read@1"]
        assert agents[reference].input_schema["required"] == ["documentText"]
