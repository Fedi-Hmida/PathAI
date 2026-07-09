from __future__ import annotations

import pytest

from app.agents.deterministic.critic import build_critic_output
from app.agents.deterministic.curriculum import build_curriculum_output
from app.agents.llm.critic import LLMCriticAgent
from app.agents.llm.curriculum import LLMCurriculumAgent
from app.agents.services.activation.errors import ActivationConfigError
from app.api.v1.dependencies import ApiServiceContainer
from app.core.settings import get_settings
from app.fixtures import canonical_demo as demo
from app.llm.contracts import RawLLMResponse, StructuredOutputRequest
from app.llm.fake_client import FakeLLMClient
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo
from app.schemas.critic import CriticAgentInput, CriticAgentOutput
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput
from app.schemas.enums import OrchestrationStatus

_SENTINEL_CURRICULUM_TITLE = "SENTINEL_HANDOFF_TITLE_FOR_REBUILD_22C_INTERACTION_TEST"


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    # get_settings() is @lru_cache'd; without clearing, monkeypatched env vars
    # in this file either read stale cached settings or leak into later tests.
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_curriculum_and_critic_flags_resolve_to_both_llm_agents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CURRICULUM_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)

    curriculum_agent = context.agent_services.curriculum.agent
    critic_agent = context.agent_services.critic.agent
    assert isinstance(curriculum_agent, LLMCurriculumAgent)
    assert isinstance(critic_agent, LLMCriticAgent)
    assert isinstance(curriculum_agent.client, FakeLLMClient)
    assert isinstance(critic_agent.client, FakeLLMClient)
    # Each agent gets its own client instance — nothing shared between them
    # except the run-scoped observer (Rebuild-22B).
    assert curriculum_agent.client is not critic_agent.client


def test_critic_consumes_curriculums_real_llm_output_not_a_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CURRICULUM_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)
    curriculum_agent = context.agent_services.curriculum.agent
    critic_agent = context.agent_services.critic.agent
    assert isinstance(curriculum_agent, LLMCurriculumAgent)
    assert isinstance(critic_agent, LLMCriticAgent)
    curriculum_client = curriculum_agent.client
    critic_client = critic_agent.client
    assert isinstance(curriculum_client, FakeLLMClient)
    assert isinstance(critic_client, FakeLLMClient)

    curriculum_client.payloads[CurriculumAgentOutput.__name__] = _sentinel_curriculum_payload()
    critic_client.payloads[CriticAgentOutput.__name__] = _critic_payload()

    captured_prompts: list[str] = []
    original_generate = critic_client.generate

    async def _spy_generate(request: StructuredOutputRequest) -> RawLLMResponse:
        captured_prompts.append(request.prompt)
        return await original_generate(request)

    monkeypatch.setattr(critic_client, "generate", _spy_generate)

    result = run_straight_line_demo(context)

    assert result.state.status == OrchestrationStatus.COMPLETED
    assert curriculum_client.call_count == 1
    assert critic_client.call_count == 1
    # The real proof: the critic's own LLM call embedded the curriculum
    # agent's *real* output — not demo.CURRICULUM's title, not the
    # deterministic build_curriculum_output() title, but the sentinel this
    # test seeded into the curriculum agent's client.
    assert any(_SENTINEL_CURRICULUM_TITLE in prompt for prompt in captured_prompts)


def test_assessment_and_knowledge_map_remain_deterministic_when_only_critic_and_curriculum_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CURRICULUM_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)

    bundle = context.agent_services
    assert type(bundle.assessment.agent).__name__ == "MockAssessorAgent"
    assert type(bundle.knowledge_map.agent).__name__ == "MockKnowledgeMapAgent"


def test_non_allowlisted_two_flag_combination_still_fails_through_orchestration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_ASSESSMENT_AGENT", "true")
    monkeypatch.setenv("PATHAI_ENABLE_LLM_CRITIC_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()

    with pytest.raises(ActivationConfigError) as exc_info:
        OrchestrationContext.from_container(container)

    message = str(exc_info.value)
    assert "assessment_agent_mode" in message
    assert "critic_agent_mode" in message


def _curriculum_input() -> CurriculumAgentInput:
    return CurriculumAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        learner_profile=demo.LEARNING_GOAL.learner_profile,
        knowledge_map=demo.KNOWLEDGE_MAP,
        duration_weeks=demo.CURRICULUM.duration_weeks,
        hours_per_week=demo.LEARNING_GOAL.hours_per_week,
        critic_recommendations=[],
    )


def _sentinel_curriculum_payload() -> dict[str, object]:
    output = build_curriculum_output(_curriculum_input())
    sentinel_output = output.model_copy(update={"title": _SENTINEL_CURRICULUM_TITLE})
    return sentinel_output.model_dump(mode="json")


def _critic_input() -> CriticAgentInput:
    return CriticAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        knowledge_map=demo.KNOWLEDGE_MAP,
        curriculum=demo.CURRICULUM,
        resource_attachments=demo.RESOURCE_ATTACHMENTS,
        rubric_weights={},
    )


def _critic_payload() -> dict[str, object]:
    return build_critic_output(_critic_input()).model_dump(mode="json")
