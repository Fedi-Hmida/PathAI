from __future__ import annotations

import pytest

from app.agents.deterministic.assessment import assessment_confidence, concept_evidence_from_answers
from app.agents.services import build_mock_agent_service_bundle
from app.agents.services.assessment import (
    AssessmentAgentService,
    AssessmentQuestionMismatchError,
    AssessmentSessionNotActiveError,
)
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.assessment import AssessmentAnswerCreate
from app.schemas.enums import AssessmentStatus


def _build_assessment_agent_service(container: ApiServiceContainer) -> AssessmentAgentService:
    return build_mock_agent_service_bundle(
        goals=container.goal_service,
        assessments=container.assessment_service,
        knowledge_maps=container.knowledge_map_service,
        curricula=container.curriculum_service,
        resources=container.resource_service,
        critics=container.critic_service,
        progress=container.progress_service,
        quizzes=container.quiz_service,
        adaptations=container.adaptation_service,
        evaluations=container.evaluation_service,
    ).assessment


def test_start_generates_a_pending_first_question() -> None:
    container = ApiServiceContainer()
    agents = _build_assessment_agent_service(container)
    goal = container.goal_service.create(demo.LEARNING_GOAL)

    session = agents.start(goal)

    assert session.status == AssessmentStatus.IN_PROGRESS
    assert session.question_count == 0
    assert session.current_question is not None


def test_start_is_idempotent_for_the_same_goal() -> None:
    container = ApiServiceContainer()
    agents = _build_assessment_agent_service(container)
    goal = container.goal_service.create(demo.LEARNING_GOAL)

    first = agents.start(goal)
    second = agents.start(goal)

    assert first.assessment_session_id == second.assessment_session_id


def test_full_turn_by_turn_diagnostic_reaches_completed_with_no_repeated_questions() -> None:
    container = ApiServiceContainer()
    agents = _build_assessment_agent_service(container)
    goal = container.goal_service.create(demo.LEARNING_GOAL)

    session = agents.start(goal)
    seen_question_ids = [session.current_question.question_id]  # type: ignore[union-attr]

    for turn in range(5):
        assert session.current_question is not None
        answer_create = AssessmentAnswerCreate(question_id=session.current_question.question_id)
        session, scored_answer = agents.submit_answer(
            goal=goal,
            session=session,
            answer_create=answer_create,
        )
        assert scored_answer.assessment_session_id == session.assessment_session_id
        # Concept evidence/confidence must update every turn, not only on the
        # final answer - the frontend's live sidebar reads this mid-session.
        assert session.concept_evidence, f"no concept evidence after turn {turn + 1}"
        if session.current_question is not None:
            seen_question_ids.append(session.current_question.question_id)

    assert session.status == AssessmentStatus.COMPLETED
    assert session.question_count == 5
    assert session.current_question is None
    assert len(seen_question_ids) == len(set(seen_question_ids))

    answers = container.assessment_service.list_answers_by_session_id(
        session.assessment_session_id,
    )
    expected_evidence = concept_evidence_from_answers(answers, goal.learner_profile)
    expected_confidence = assessment_confidence(
        answer_count=len(answers),
        evidence_count=len(expected_evidence),
    )
    assert session.confidence == expected_confidence
    assert [e.concept_id for e in session.concept_evidence] == [
        e.concept_id for e in expected_evidence
    ]


def test_submitting_a_stale_question_id_is_rejected() -> None:
    container = ApiServiceContainer()
    agents = _build_assessment_agent_service(container)
    goal = container.goal_service.create(demo.LEARNING_GOAL)

    session = agents.start(goal)
    assert session.current_question is not None
    stale_answer = AssessmentAnswerCreate(question_id="question_does_not_match_pending")

    with pytest.raises(AssessmentQuestionMismatchError):
        agents.submit_answer(goal=goal, session=session, answer_create=stale_answer)


def test_submitting_after_completion_is_rejected() -> None:
    container = ApiServiceContainer()
    agents = _build_assessment_agent_service(container)
    goal = container.goal_service.create(demo.LEARNING_GOAL)

    session = agents.start(goal)
    for _ in range(5):
        assert session.current_question is not None
        answer_create = AssessmentAnswerCreate(question_id=session.current_question.question_id)
        session, _ = agents.submit_answer(goal=goal, session=session, answer_create=answer_create)

    assert session.status == AssessmentStatus.COMPLETED
    late_answer = AssessmentAnswerCreate(question_id="question_assess_retriever_role")

    with pytest.raises(AssessmentSessionNotActiveError):
        agents.submit_answer(goal=goal, session=session, answer_create=late_answer)
