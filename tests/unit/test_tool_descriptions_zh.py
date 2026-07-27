from __future__ import annotations

import re

from swarmcore_registry import builtin_registry

_CJK = re.compile(r"[\u4e00-\u9fff]")
_ENGLISH_VERB = re.compile(
    r"\b(Search|Publish|Read|Evaluate|Render|Aggregate|Research|Analyze|Extract|Write|Review|Act)\b"
)


def test_builtin_tool_descriptions_are_chinese() -> None:
    tools = builtin_registry().tools
    assert tools
    for tool in tools:
        assert _CJK.search(tool.description), (
            f"{tool.ref} description should be Chinese: {tool.description!r}"
        )
        assert not _ENGLISH_VERB.search(tool.description), (
            f"{tool.ref} still looks English: {tool.description!r}"
        )


def test_builtin_agent_display_descriptions_are_short_chinese() -> None:
    agents = builtin_registry().agents
    assert agents
    for agent in agents:
        assert _CJK.search(agent.description), (
            f"{agent.ref} description should be Chinese: {agent.description!r}"
        )
        assert not _ENGLISH_VERB.search(agent.description), (
            f"{agent.ref} still looks English: {agent.description!r}"
        )
        assert "\n" not in agent.description
        assert 8 <= len(agent.description) <= 48, (
            f"{agent.ref} description length out of range: {agent.description!r}"
        )
        assert agent.instructions != agent.description
        assert len(agent.instructions) > len(agent.description)


def test_builtin_model_descriptions_are_chinese() -> None:
    models = builtin_registry().models
    assert models
    for model in models:
        assert _CJK.search(model.description), (
            f"{model.ref} description should be Chinese: {model.description!r}"
        )
        assert not model.description.startswith("Model route for ")


def test_search_tool_description_is_expected_chinese() -> None:
    tool = builtin_registry().resolve_tool("tool://search@1")
    assert tool is not None
    assert tool.description == "在已配置的知识源中检索内容。"


def test_post_evaluation_agent_display_description() -> None:
    agent = builtin_registry().resolve_agent("agent://contract/post-evaluation-analyst@1")
    assert agent is not None
    assert agent.description == "基于上传文件与流程说明，生成规范化的合同后评价结果。"
    assert agent.instructions.startswith("Read every supplied file")
