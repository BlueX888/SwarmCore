import pytest
from pydantic import ValidationError
from swarmcore_api.schemas import CreateRunRequest


def test_run_request_requires_exactly_one_strategy_source() -> None:
    version = "00000000-0000-0000-0000-000000000001"
    assert CreateRunRequest.model_validate({"strategyVersionId": version}).spec is None
    assert CreateRunRequest.model_validate({"spec": {}}).strategy_version_id is None
    with pytest.raises(ValidationError):
        CreateRunRequest.model_validate({})
    with pytest.raises(ValidationError):
        CreateRunRequest.model_validate({"strategyVersionId": version, "spec": {}})
