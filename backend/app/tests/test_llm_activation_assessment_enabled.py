from __future__ import annotations

import pytest

from app.agents.deterministic.assessment import (
    build_question_output,
    diagnostic_focus_for_goal,
    seeded_answer_for_question,
)
from app.agents.deterministic.assessment import score_answer as deterministic_score_answer
from app.agents.llm.assessment import LLMAssessmentAgent
from app.api.v1.dependencies import ApiServiceContainer
from app.core.settings import get_settings
from app.fixtures import canonical_demo as demo
from app.llm.fake_client import FakeLLMClient
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo
from app.schemas.assessment import (
    AssessmentAgentInput,
    AssessmentAgentOutput,
    AssessmentScoreOutput,
)
from app.schemas.enums import OrchestrationStatus


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    # get_settings() is @lru_cache'd; without clearing, monkeypatched env vars
    # in this file either read stale cached settings or leak into later tests.
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_assessment_flag_switches_orchestration_default_to_llm_agent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_ASSESSMENT_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)

    assessment_agent = context.agent_services.assessment.agent
    assert isinstance(assessment_agent, LLMAssessmentAgent)
    assert isinstance(assessment_agent.client, FakeLLMClient)


def test_assessment_flag_produces_valid_output_end_to_end(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_ASSESSMENT_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)
    assessment_agent = context.agent_services.assessment.agent
    assert isinstance(assessment_agent, LLMAssessmentAgent)
    fake_client = assessment_agent.client
    assert isinstance(fake_client, FakeLLMClient)
    fake_client.payloads[AssessmentAgentOutput.__name__] = _fake_question_payload()
    fake_client.payloads[AssessmentScoreOutput.__name__] = _fake_score_payload()

    result = run_straight_line_demo(context)

    assert result.state.status == OrchestrationStatus.COMPLETED
    # run_diagnostic asks 5 questions and scores 5 answers per full session.
    assert fake_client.call_count == 10


def test_other_three_agents_remain_deterministic_when_only_assessment_flag_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_LLM_ASSESSMENT_AGENT", "true")
    monkeypatch.setenv("LLM_PROVIDER", "fake")

    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)

    bundle = context.agent_services
    assert type(bundle.knowledge_map.agent).__name__ == "MockKnowledgeMapAgent"
    assert type(bundle.critic.agent).__name__ == "MockCriticAgent"
    assert type(bundle.curriculum.agent).__name__ == "MockCurriculumAgent"


def test_flag_left_unset_still_resolves_to_deterministic_default() -> None:
    # No monkeypatch in this test — guards against cache-clear alone leaking
    # a previous test's env state back in.
    container = ApiServiceContainer()

    context = OrchestrationContext.from_container(container)

    assert type(context.agent_services.assessment.agent).__name__ == "MockAssessorAgent"


def _question_input() -> AssessmentAgentInput:
    return AssessmentAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        learner_profile=demo.LEARNING_GOAL.learner_profile,
        prior_answers=[],
        target_concepts=diagnostic_focus_for_goal(
            demo.LEARNING_GOAL.goal_text,
            demo.LEARNING_GOAL.learner_profile,
        ),
        current_confidence=0.0,
        question_count=0,
    )


def _fake_question_payload() -> dict[str, object]:
    return build_question_output(_question_input()).model_dump(mode="json")


def _fake_score_payload() -> dict[str, object]:
    question_output = build_question_output(_question_input())
    answer = seeded_answer_for_question(
        goal=demo.LEARNING_GOAL,
        question=question_output.question,
    )
    return deterministic_score_answer(answer).model_dump(mode="json")
