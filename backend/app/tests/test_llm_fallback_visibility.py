from __future__ import annotations

import pytest

from app.agents.deterministic.assessment import build_question_output, score_answer
from app.agents.deterministic.critic import build_critic_output
from app.agents.deterministic.curriculum import build_curriculum_output
from app.agents.deterministic.knowledge_map import build_knowledge_map_output
from app.agents.errors import LLMGenerationUnavailableError
from app.agents.llm.assessment import LLMAssessmentAgent
from app.agents.llm.critic import LLMCriticAgent
from app.agents.llm.curriculum import LLMCurriculumAgent
from app.agents.llm.knowledge_map import LLMKnowledgeMapAgent
from app.agents.mock import (
    MockAssessorAgent,
    MockCriticAgent,
    MockCurriculumAgent,
    MockKnowledgeMapAgent,
)
from app.fixtures import canonical_demo as demo
from app.llm import FakeLLMClient, FakeLLMScenario, LLMRetryPolicy
from app.llm.observability.sinks import CountingObserver
from app.schemas.assessment import AssessmentAgentInput
from app.schemas.critic import CriticAgentInput
from app.schemas.curriculum import CurriculumAgentInput
from app.schemas.knowledge_map import KnowledgeMapAgentInput

_NO_DELAY_SINGLE_ATTEMPT = LLMRetryPolicy(max_attempts=1, backoff_seconds=0)


def _event_type_counts(observer: CountingObserver) -> dict[str, int]:
    counts = observer.safe_summary()["counts_by_event_type"]
    assert isinstance(counts, dict)
    return counts


def test_knowledge_map_agent_records_fallback_used_event() -> None:
    observer = CountingObserver()
    agent = LLMKnowledgeMapAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR),
        fallback_agent=MockKnowledgeMapAgent(),
        fallback_on_error=True,
        retry_policy=_NO_DELAY_SINGLE_ATTEMPT,
        observer=observer,
    )
    payload = _knowledge_map_input()

    output = agent.build_knowledge_map(payload)

    assert output == build_knowledge_map_output(payload)
    assert _event_type_counts(observer)["fallback_used"] == 1


def test_knowledge_map_agent_without_fallback_fails_loud_records_event() -> None:
    observer = CountingObserver()
    agent = LLMKnowledgeMapAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR),
        fallback_agent=None,
        fallback_on_error=True,
        retry_policy=_NO_DELAY_SINGLE_ATTEMPT,
        observer=observer,
    )

    with pytest.raises(LLMGenerationUnavailableError):
        agent.build_knowledge_map(_knowledge_map_input())

    counts = _event_type_counts(observer)
    assert counts["retry_exhausted"] == 1
    # The fail-loud path emits its own distinct, secret-free reliability event
    # so operators can see the real failure without a silent fallback.
    assert counts["generation_unavailable"] == 1
    assert "fallback_used" not in counts


def test_knowledge_map_agent_default_observer_is_inert() -> None:
    agent = LLMKnowledgeMapAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR),
        fallback_agent=MockKnowledgeMapAgent(),
        fallback_on_error=True,
        retry_policy=_NO_DELAY_SINGLE_ATTEMPT,
    )

    output = agent.build_knowledge_map(_knowledge_map_input())

    assert output is not None


def test_critic_agent_records_fallback_used_event() -> None:
    observer = CountingObserver()
    agent = LLMCriticAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR),
        fallback_agent=MockCriticAgent(),
        fallback_on_error=True,
        retry_policy=_NO_DELAY_SINGLE_ATTEMPT,
        observer=observer,
    )
    payload = _critic_input()

    output = agent.review_curriculum(payload)

    assert output == build_critic_output(payload)
    assert _event_type_counts(observer)["fallback_used"] == 1


def test_curriculum_agent_records_fallback_used_event() -> None:
    observer = CountingObserver()
    agent = LLMCurriculumAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR),
        fallback_agent=MockCurriculumAgent(),
        fallback_on_error=True,
        retry_policy=_NO_DELAY_SINGLE_ATTEMPT,
        observer=observer,
    )
    payload = _curriculum_input()

    output = agent.build_curriculum(payload)

    assert output.duration_weeks == build_curriculum_output(payload).duration_weeks
    assert _event_type_counts(observer)["fallback_used"] == 1


def test_assessment_agent_records_fallback_used_event_for_question() -> None:
    observer = CountingObserver()
    agent = LLMAssessmentAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR),
        fallback_agent=MockAssessorAgent(),
        fallback_on_error=True,
        retry_policy=_NO_DELAY_SINGLE_ATTEMPT,
        observer=observer,
    )
    payload = _assessment_agent_input()

    output = agent.generate_question(payload)

    assert output.question.question_id == build_question_output(payload).question.question_id
    assert _event_type_counts(observer)["fallback_used"] == 1


def test_assessment_agent_records_fallback_used_event_for_scoring() -> None:
    observer = CountingObserver()
    agent = LLMAssessmentAgent(
        client=FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR),
        fallback_agent=MockAssessorAgent(),
        fallback_on_error=True,
        retry_policy=_NO_DELAY_SINGLE_ATTEMPT,
        observer=observer,
    )
    answer = demo.ASSESSMENT_ANSWERS[0].model_copy(deep=True)

    output = agent.score_answer(answer)

    assert output.answer_id == score_answer(answer).answer_id
    assert _event_type_counts(observer)["fallback_used"] == 1


def _knowledge_map_input() -> KnowledgeMapAgentInput:
    return KnowledgeMapAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        assessment_answers=demo.ASSESSMENT_ANSWERS,
        concept_evidence=demo.ASSESSMENT_SESSION.concept_evidence,
    )


def _critic_input() -> CriticAgentInput:
    return CriticAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        knowledge_map=demo.KNOWLEDGE_MAP,
        curriculum=demo.CURRICULUM,
        resource_attachments=demo.RESOURCE_ATTACHMENTS,
        rubric_weights={},
    )


def _curriculum_input() -> CurriculumAgentInput:
    return CurriculumAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        learner_profile=demo.LEARNING_GOAL.learner_profile,
        knowledge_map=demo.KNOWLEDGE_MAP,
        duration_weeks=demo.CURRICULUM.duration_weeks,
        hours_per_week=demo.LEARNING_GOAL.hours_per_week,
        critic_recommendations=[],
    )


def _assessment_agent_input() -> AssessmentAgentInput:
    return AssessmentAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        learner_profile=demo.LEARNING_GOAL.learner_profile,
        prior_answers=[],
        target_concepts=["rag_fundamentals", "retrieval_evaluation"],
        current_confidence=0.0,
        question_count=0,
    )
