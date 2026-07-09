from __future__ import annotations

import pytest

from app.agents.deterministic.curriculum import build_curriculum_output
from app.agents.llm.curriculum import LLMCurriculumAgent
from app.api.v1.dependencies import ApiServiceContainer
from app.core.settings import get_settings
from app.fixtures import canonical_demo as demo
from app.llm.fake_client import FakeLLMClient
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput
from app.schemas.enums import OrchestrationStatus


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    # get_settings() is @lru_cache'd; without clearing, monkeypatched env vars
    # in this file either read stale cached settings or leak into later tests.
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_curriculum_flag_switches_orchestration_default_to_llm_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CURRICULUM_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)

    curriculum_agent = context.agent_services.curriculum.agent
    assert isinstance(curriculum_agent, LLMCurriculumAgent)
    assert isinstance(curriculum_agent.client, FakeLLMClient)


def test_curriculum_flag_produces_valid_output_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CURRICULUM_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)
    curriculum_agent = context.agent_services.curriculum.agent
    assert isinstance(curriculum_agent, LLMCurriculumAgent)
    fake_client = curriculum_agent.client
    assert isinstance(fake_client, FakeLLMClient)
    fake_client.payloads[CurriculumAgentOutput.__name__] = _fake_curriculum_payload()

    result = run_straight_line_demo(context)

    assert result.state.status == OrchestrationStatus.COMPLETED
    assert fake_client.call_count == 1


def test_other_three_agents_remain_deterministic_when_only_curriculum_flag_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CURRICULUM_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)

    bundle = context.agent_services
    assert type(bundle.assessment.agent).__name__ == "MockAssessorAgent"
    assert type(bundle.knowledge_map.agent).__name__ == "MockKnowledgeMapAgent"
    assert type(bundle.critic.agent).__name__ == "MockCriticAgent"


def test_flag_left_unset_still_resolves_to_deterministic_default() -> None:
    # No monkeypatch in this test — guards against cache-clear alone leaking
    # a previous test's env state back in.
    container = ApiServiceContainer()

    context = OrchestrationContext.from_container(container)

    assert type(context.agent_services.curriculum.agent).__name__ == "MockCurriculumAgent"


def _curriculum_input() -> CurriculumAgentInput:
    return CurriculumAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        learner_profile=demo.LEARNING_GOAL.learner_profile,
        knowledge_map=demo.KNOWLEDGE_MAP,
        duration_weeks=demo.CURRICULUM.duration_weeks,
        hours_per_week=demo.LEARNING_GOAL.hours_per_week,
        critic_recommendations=[],
    )


def _fake_curriculum_payload() -> dict[str, object]:
    return build_curriculum_output(_curriculum_input()).model_dump(mode="json")
