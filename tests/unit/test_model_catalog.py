from datetime import UTC, datetime, timedelta

from swarmcore_application import CapabilityCatalogService
from swarmcore_model_gateway.main import (
    ModelProviderConfigurationBody,
    _active_model_reservations,
    _reserved_tokens,
    _tested_provider_matches,
)
from swarmcore_model_gateway.main import (
    Settings as ModelGatewaySettings,
)
from swarmcore_registry import builtin_registry
from swarmcore_worker_agent.main import Settings as AgentWorkerSettings

SUPPORTED_MODELS = {
    "model://deepseek-v4-flash": "DeepSeek-V4-Flash",
    "model://deepseek-v4-pro": "DeepSeek-V4-Pro",
    "model://kimi-k2.5": "kimi-k2.5",
    "model://kimi-k2.7-code": "kimi-k2.7-code",
}


def test_expired_model_reservations_do_not_consume_budget() -> None:
    now = datetime(2026, 7, 29, tzinfo=UTC)
    active = _active_model_reservations(
        {
            "expired": {
                "tokens": 900,
                "expiresAt": (now - timedelta(seconds=1)).isoformat(),
            },
            "active": {
                "tokens": 100,
                "expiresAt": (now + timedelta(seconds=1)).isoformat(),
            },
        },
        now=now,
        legacy_ttl_seconds=360,
    )

    assert set(active) == {"active"}
    assert _reserved_tokens(active) == 100


def test_agent_worker_default_output_budget_supports_large_structured_results() -> None:
    assert AgentWorkerSettings(_env_file=None).agent_model_max_output_tokens == 16384


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

    assert set(agents) >= {
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
    assert set(agents) >= {
        "agent://invoice/commercial-match-analyst@1",
        "agent://invoice/evidence-risk-reviewer@1",
        "agent://invoice/fact-normalizer@1",
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


def test_connectivity_result_only_verifies_the_matching_saved_provider() -> None:
    body = ModelProviderConfigurationBody(
        logicalModel="model://general",
        providerUrl="https://api.example.com/v1",
        modelName="provider-model",
    )
    assert _tested_provider_matches(
        provider_url="https://api.example.com/v1/",
        model_name="provider-model",
        saved_api_key="saved-key",
        body=body,
        tested_api_key="saved-key",
    )
    assert not _tested_provider_matches(
        provider_url="https://api.example.com/v1",
        model_name="provider-model",
        saved_api_key="saved-key",
        body=body,
        tested_api_key="different-key",
    )
