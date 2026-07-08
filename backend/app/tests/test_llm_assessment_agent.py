from __future__ import annotations

from app.agents.deterministic.assessment import build_question_output, score_answer
from app.agents.llm.assessment import LLMAssessmentAgent
from app.agents.mock import MockAssessorAgent
from app.agents.services import (
    AgentIntegrationSwitches,
    AssessmentAgentMode,
    AssessmentAgentService,
    build_mock_agent_service_bundle,
)
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.llm import FakeLLMClient
from app.schemas.assessment import (
    AssessmentAgentInput,
    AssessmentAgentOutput,
    AssessmentAnswerDTO,
    AssessmentScoreOutput,
)


def test_llm_assessment_agent_uses_fake_structured_output_for_question() -> None:
    payload = _question_payload()
    client = _fake_assessment_client(payload)
    agent = LLMAssessmentAgent(
        client=client,
        fallback_agent=MockAssessorAgent(),
    )

    output = agent.generate_question(_assessment_agent_input())

    assert output.question.question_id == payload.question.question_id
    assert output.rationale == payload.rationale
    assert client.call_count == 1


def test_llm_assessment_agent_uses_fake_structured_output_for_scoring() -> None:
    payload = _scoring_payload()
    client = _fake_assessment_client(payload)
    agent = LLMAssessmentAgent(
        client=client,
        fallback_agent=MockAssessorAgent(),
    )

    answer = _sample_answer()
    output = agent.score_answer(answer)

    assert output.answer_id == payload.answer_id
    assert output.score == payload.score
    assert client.call_count == 1


def test_llm_assessment_agent_falls_back_on_error() -> None:
    from app.llm.fake_client import FakeLLMScenario

    client = FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR)
    fallback = MockAssessorAgent()
    agent = LLMAssessmentAgent(
        client=client,
        fallback_agent=fallback,
        fallback_on_error=True,
    )

    output = agent.generate_question(_assessment_agent_input())

    assert output is not None
    assert client.call_count >= 1


def test_llm_assessment_service_persists_validated_question_output() -> None:
    container = ApiServiceContainer()
    payload = _question_payload()
    agent = LLMAssessmentAgent(
        client=_fake_assessment_client(payload),
        fallback_agent=MockAssessorAgent(),
    )
    service = AssessmentAgentService(agent, container.assessment_service)

    goal = container.goal_service.create(demo.LEARNING_GOAL)
    output = service._generate_question(
        goal=goal,
        target_concepts=["rag_fundamentals", "retrieval_evaluation"],
        prior_answers=[],
    )

    assert output.question.question_id == payload.question.question_id
    assert output.rationale == payload.rationale


def test_llm_assessment_service_persists_validated_scoring_output() -> None:
    payload = _scoring_payload()
    agent = LLMAssessmentAgent(
        client=_fake_assessment_client(payload),
        fallback_agent=MockAssessorAgent(),
    )

    answer = _sample_answer()
    score_output = agent.score_answer(answer)

    assert score_output.answer_id == payload.answer_id
    assert score_output.score == payload.score


def test_agent_bundle_can_switch_assessment_to_injected_llm_agent() -> None:
    container = ApiServiceContainer()
    payload = _question_payload()
    llm_agent = LLMAssessmentAgent(
        client=_fake_assessment_client(payload),
        fallback_agent=MockAssessorAgent(),
    )

    agents = build_mock_agent_service_bundle(
        assessments=container.assessment_service,
        knowledge_maps=container.knowledge_map_service,
        curricula=container.curriculum_service,
        resources=container.resource_service,
        critics=container.critic_service,
        progress=container.progress_service,
        quizzes=container.quiz_service,
        adaptations=container.adaptation_service,
        evaluations=container.evaluation_service,
        switches=AgentIntegrationSwitches(
            assessment_agent_mode=AssessmentAgentMode.LLM,
        ),
        assessment_agent=llm_agent,
    )

    assert agents.assessment.agent is llm_agent


def test_agent_bundle_defaults_to_deterministic_assessment_agent() -> None:
    container = ApiServiceContainer()

    agents = build_mock_agent_service_bundle(
        assessments=container.assessment_service,
        knowledge_maps=container.knowledge_map_service,
        curricula=container.curriculum_service,
        resources=container.resource_service,
        critics=container.critic_service,
        progress=container.progress_service,
        quizzes=container.quiz_service,
        adaptations=container.adaptation_service,
        evaluations=container.evaluation_service,
        switches=AgentIntegrationSwitches(),
    )

    assert isinstance(agents.assessment.agent, MockAssessorAgent)


def _assessment_agent_input() -> AssessmentAgentInput:
    return AssessmentAgentInput(
        goal_text=demo.LEARNING_GOAL.goal_text,
        learner_profile=demo.LEARNING_GOAL.learner_profile,
        prior_answers=[],
        target_concepts=["rag_fundamentals", "retrieval_evaluation"],
        current_confidence=0.0,
        question_count=0,
    )


def _question_payload() -> AssessmentAgentOutput:
    base_output = build_question_output(_assessment_agent_input())
    return base_output.model_copy(
        update={
            "rationale": (
                "LLM-backed fake path validates retrieval fundamentals and "
                "evaluation metrics."
            ),
        },
        deep=True,
    )


def _scoring_payload() -> AssessmentScoreOutput:
    answer = _sample_answer()
    base_output = score_answer(answer)
    return base_output.model_copy(
        update={
            "score": 0.85,
            "feedback": "LLM-backed fake scoring confirms strong retrieval understanding.",
        },
        deep=True,
    )


def _sample_answer() -> AssessmentAnswerDTO:
    return demo.ASSESSMENT_ANSWERS[0].model_copy(deep=True)


def _fake_assessment_client(
    payload: AssessmentAgentOutput | AssessmentScoreOutput,
) -> FakeLLMClient:
    payloads = {}
    if isinstance(payload, AssessmentAgentOutput):
        payloads[AssessmentAgentOutput.__name__] = payload.model_dump(mode="json")
    elif isinstance(payload, AssessmentScoreOutput):
        payloads[AssessmentScoreOutput.__name__] = payload.model_dump(mode="json")
    return FakeLLMClient(payloads=payloads)
