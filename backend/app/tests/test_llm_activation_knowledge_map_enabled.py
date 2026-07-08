from __future__ import annotations

import pytest

from app.agents.deterministic.knowledge_map import build_knowledge_map_output
from app.agents.llm.knowledge_map import LLMKnowledgeMapAgent
from app.api.v1.dependencies import ApiServiceContainer
from app.core.settings import get_settings
from app.fixtures import canonical_demo as demo
from app.llm.fake_client import FakeLLMClient
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo
from app.schemas.enums import OrchestrationStatus
from app.schemas.knowledge_map import KnowledgeMapAgentInput, KnowledgeMapAgentOutput


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    # get_settings() is @lru_cache'd; without clearing, monkeypatched env vars
    # in this file either read stale cached settings or leak into later tests.
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_knowledge_map_flag_switches_orchestration_default_to_llm_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)

    knowledge_map_agent = context.agent_services.knowledge_map.agent
    assert isinstance(knowledge_map_agent, LLMKnowledgeMapAgent)
    assert isinstance(knowledge_map_agent.client, FakeLLMClient)


def test_knowledge_map_flag_produces_valid_output_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)
    knowledge_map_agent = context.agent_services.knowledge_map.agent
    assert isinstance(knowledge_map_agent, LLMKnowledgeMapAgent)
    fake_client = knowledge_map_agent.client
    assert isinstance(fake_client, FakeLLMClient)
    fake_client.payloads[KnowledgeMapAgentOutput.__name__] = _fake_knowledge_map_payload()

    result = run_straight_line_demo(context)

    assert result.state.status == OrchestrationStatus.COMPLETED
    assert fake_client.call_count == 1


def test_other_three_agents_remain_deterministic_when_only_knowledge_map_flag_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)

    bundle = context.agent_services
    assert type(bundle.assessment.agent).__name__ == "MockAssessorAgent"
    assert type(bundle.critic.agent).__name__ == "MockCriticAgent"
    assert type(bundle.curriculum.agent).__name__ == "MockCurriculumAgent"


def test_flag_left_unset_still_resolves_to_deterministic_default() -> None:
    # No monkeypatch in this test — guards against cache-clear alone leaking
    # a previous test's env state back in.
    container = ApiServiceContainer()

    context = OrchestrationContext.from_container(container)

    assert type(context.agent_services.knowledge_map.agent).__name__ == "MockKnowledgeMapAgent"


def _knowledge_map_input() -> KnowledgeMapAgentInput:
    return KnowledgeMapAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        assessment_answers=demo.ASSESSMENT_ANSWERS,
        concept_evidence=demo.ASSESSMENT_SESSION.concept_evidence,
    )


def _fake_knowledge_map_payload() -> dict[str, object]:
    return build_knowledge_map_output(_knowledge_map_input()).model_dump(mode="json")
