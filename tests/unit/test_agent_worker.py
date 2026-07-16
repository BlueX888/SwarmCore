import pytest
from swarmcore_worker_agent import StaticModelResolver


def test_model_resolver_only_allows_registered_references() -> None:
    resolver = StaticModelResolver({"model://general": "openai:gpt-4o-mini"})
    assert resolver.resolve("model://general") == "openai:gpt-4o-mini"
    with pytest.raises(ValueError, match="not configured"):
        resolver.resolve("model://unregistered")
