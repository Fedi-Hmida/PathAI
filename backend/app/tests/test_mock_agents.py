from __future__ import annotations

import pytest

from app.agents.errors import ControlledAgentFailure
from app.agents.mock import (
    MockAdapterAgent,
    MockAssessorAgent,
    MockCriticAgent,
    MockCurriculumAgent,
    MockEvaluationAgent,
    MockKnowledgeMapAgent,
    MockProgressAgent,
    MockQuizAgent,
    MockResourceAgent,
)
from app.fixtures import canonical_demo as demo
from app.schemas.adaptation import AdaptationAgentInput, AdaptationAgentOutput
from app.schemas.assessment import AssessmentAgentInput, AssessmentAgentOutput
from app.schemas.critic import CriticAgentInput, CriticAgentOutput
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput
from app.schemas.evaluation import EvaluationAgentInput, EvaluationAgentOutput
from app.schemas.knowledge_map import KnowledgeMapAgentInput, KnowledgeMapAgentOutput
from app.schemas.quiz import QuizAgentInput, QuizAgentOutput
from app.schemas.resource import ResourceAgentInput, ResourceAgentOutput


def test_mock_agents_return_schema_valid_stable_outputs() -> None:
    assessment_input = AssessmentAgentInput(
        goal_text=demo.CANONICAL_GOAL_TEXT,
        learner_profile=demo.LEARNER_PROFILE,
        target_concepts=["rag_fundamentals"],
        current_confidence=0.0,
        question_count=0,
    )
    assessment_one = MockAssessorAgent().generate_question(assessment_input)
    assessment_two = MockAssessorAgent().generate_question(assessment_input)
    assert AssessmentAgentOutput.model_validate(assessment_one) == assessment_two

    knowledge_input = KnowledgeMapAgentInput(
        goal_text=demo.CANONICAL_GOAL_TEXT,
        assessment_answers=demo.ASSESSMENT_ANSWERS,
        concept_evidence=demo.ASSESSMENT_SESSION.concept_evidence,
    )
    assert isinstance(
        MockKnowledgeMapAgent().build_knowledge_map(knowledge_input),
        KnowledgeMapAgentOutput,
    )

    curriculum_input = CurriculumAgentInput(
        goal_text=demo.CANONICAL_GOAL_TEXT,
        learner_profile=demo.LEARNER_PROFILE,
        knowledge_map=demo.KNOWLEDGE_MAP,
        duration_weeks=4,
        hours_per_week=7,
    )
    assert isinstance(
        MockCurriculumAgent().build_curriculum(curriculum_input),
        CurriculumAgentOutput,
    )

    resource_input = ResourceAgentInput(
        curriculum=demo.CURRICULUM,
        knowledge_map=demo.KNOWLEDGE_MAP,
        corpus_resources=demo.RESOURCE_CORPUS,
    )
    assert isinstance(MockResourceAgent().attach_resources(resource_input), ResourceAgentOutput)

    critic_input = CriticAgentInput(
        goal_text=demo.CANONICAL_GOAL_TEXT,
        knowledge_map=demo.KNOWLEDGE_MAP,
        curriculum=demo.CURRICULUM,
        resource_attachments=demo.RESOURCE_ATTACHMENTS,
    )
    assert isinstance(MockCriticAgent().review_curriculum(critic_input), CriticAgentOutput)

    assert isinstance(
        MockProgressAgent().build_progress_state(demo.LEARNING_GOAL, demo.CURRICULUM),
        type(demo.PROGRESS_STATE),
    )

    quiz_input = QuizAgentInput(
        goal_text=demo.CANONICAL_GOAL_TEXT,
        curriculum_topics=demo.TOPICS,
        target_concepts=demo.QUIZ.target_concept_ids,
        difficulty=demo.QUIZ.difficulty,
        question_count=len(demo.QUIZ.questions),
    )
    assert isinstance(MockQuizAgent().build_quiz(quiz_input), QuizAgentOutput)

    adaptation_input = AdaptationAgentInput(
        goal_text=demo.CANONICAL_GOAL_TEXT,
        curriculum=demo.CURRICULUM,
        progress_state=demo.PROGRESS_STATE,
        quiz_attempt=demo.QUIZ_ATTEMPT,
        weak_concepts=demo.PROGRESS_STATE.weak_concepts,
    )
    assert isinstance(MockAdapterAgent().plan_adaptation(adaptation_input), AdaptationAgentOutput)

    evaluation_input = EvaluationAgentInput(
        goal=demo.LEARNING_GOAL,
        assessment=demo.ASSESSMENT_SESSION,
        knowledge_map=demo.KNOWLEDGE_MAP,
        curriculum=demo.CURRICULUM,
        resources=demo.RESOURCE_ATTACHMENTS,
        critic_review=demo.CRITIC_REVIEW,
        quiz_attempt=demo.QUIZ_ATTEMPT,
        adaptation_event=demo.ADAPTATION_EVENT,
    )
    assert isinstance(MockEvaluationAgent().evaluate_run(evaluation_input), EvaluationAgentOutput)


def test_mock_agents_return_deep_copies() -> None:
    assessment_input = AssessmentAgentInput(
        goal_text=demo.CANONICAL_GOAL_TEXT,
        learner_profile=demo.LEARNER_PROFILE,
        target_concepts=["rag_fundamentals"],
        current_confidence=0.0,
        question_count=0,
    )

    first = MockAssessorAgent().generate_question(assessment_input)
    first.question.prompt = "mutated locally"
    second = MockAssessorAgent().generate_question(assessment_input)

    assert second.question.prompt != "mutated locally"


def test_mock_agent_controlled_failure() -> None:
    assessment_input = AssessmentAgentInput(
        goal_text=demo.CANONICAL_GOAL_TEXT,
        learner_profile=demo.LEARNER_PROFILE,
        target_concepts=["rag_fundamentals"],
        current_confidence=0.0,
        question_count=0,
    )

    with pytest.raises(ControlledAgentFailure):
        MockAssessorAgent(fail=True).generate_question(assessment_input)
