from swarmcore_api.schemas import EditorState


def test_editor_state_defaults_agent_bindings_to_empty_object() -> None:
    state = EditorState.model_validate(
        {"positions": {}, "viewport": {"x": 0, "y": 0, "zoom": 1}},
    )
    assert state.agent_bindings == {}
    dumped = state.model_dump(mode="json", by_alias=True)
    assert dumped["agentBindings"] == {}


def test_editor_state_round_trips_agent_bindings() -> None:
    payload = {
        "positions": {"agent-1": {"x": 10, "y": 20}},
        "viewport": {"x": 1, "y": 2, "zoom": 0.8},
        "agentBindings": {
            "agent-1": {
                "configurationId": "cfg-1",
                "revision": 3,
                "name": "合同审查智能体",
                "sourceRef": "inline/agno",
            },
        },
    }
    state = EditorState.model_validate(payload)
    assert state.agent_bindings["agent-1"].configuration_id == "cfg-1"
    assert state.agent_bindings["agent-1"].revision == 3
    assert state.model_dump(mode="json", by_alias=True) == payload
