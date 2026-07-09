from __future__ import annotations

import pytest

from app.agents.deterministic.critic import build_critic_output
from app.agents.llm.critic import LLMCriticAgent
from app.api.v1.dependencies import ApiServiceContainer
from app.core.settings import get_settings
from app.fixtures import canonical_demo as demo
from app.llm.fake_client import FakeLLMClient
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo
from app.schemas.critic import CriticAgentInput, CriticAgentOutput
from app.schemas.enums import OrchestrationStatus


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    # get_settings() is @lru_cache'd; without clearing, monkeypatched env vars
    # in this file either read stale cached settings or leak into later tests.
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_critic_flag_switches_orchestration_default_to_llm_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)

    critic_agent = context.agent_services.critic.agent
    assert isinstance(critic_agent, LLMCriticAgent)
    assert isinstance(critic_agent.client, FakeLLMClient)


def test_critic_flag_produces_valid_output_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)
    critic_agent = context.agent_services.critic.agent
    assert isinstance(critic_agent, LLMCriticAgent)
    fake_client = critic_agent.client
    assert isinstance(fake_client, FakeLLMClient)
    fake_client.payloads[CriticAgentOutput.__name__] = _fake_critic_payload()

    result = run_straight_line_demo(context)

    assert result.state.status == OrchestrationStatus.COMPLETED
    assert fake_client.call_count == 1


def test_other_three_agents_remain_deterministic_when_only_critic_flag_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)

    bundle = context.agent_services
    assert type(bundle.assessment.agent).__name__ == "MockAssessorAgent"
    assert type(bundle.knowledge_map.agent).__name__ == "MockKnowledgeMapAgent"
    assert type(bundle.curriculum.agent).__name__ == "MockCurriculumAgent"


def test_flag_left_unset_still_resolves_to_deterministic_default() -> None:
    # No monkeypatch in this test — guards against cache-clear alone leaking
    # a previous test's env state back in.
    container = ApiServiceContainer()

    context = OrchestrationContext.from_container(container)

    assert type(context.agent_services.critic.agent).__name__ == "MockCriticAgent"


def _critic_input() -> CriticAgentInput:
    return CriticAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        knowledge_map=demo.KNOWLEDGE_MAP,
        curriculum=demo.CURRICULUM,
        resource_attachments=demo.RESOURCE_ATTACHMENTS,
        rubric_weights={},
    )


def _fake_critic_payload() -> dict[str, object]:
    return build_critic_output(_critic_input()).model_dump(mode="json")
