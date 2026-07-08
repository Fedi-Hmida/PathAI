from __future__ import annotations

from app.agents.services import build_mock_agent_service_bundle
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.enums import AssessmentStatus


def test_assessment_diagnostic_is_goal_aware_and_evidence_driven() -> None:
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
    )

    goal = container.goal_service.create(demo.LEARNING_GOAL)
    session = agents.assessment.run_diagnostic(goal)
    answers = container.assessment_service.list_answers_by_session_id(
        session.assessment_session_id,
    )

    assert session.status == AssessmentStatus.COMPLETED
    assert session.question_count == len(demo.ASSESSMENT_QUESTIONS)
    assert session.confidence >= 0.75
    assert session.termination_reason == "confidence_target_met"
    assert [answer.question.question_id for answer in answers] == [
        question.question_id
        for question in demo.ASSESSMENT_QUESTIONS
    ]

    evidence_by_concept = {
        evidence.concept_id: evidence
        for evidence in session.concept_evidence
    }
    assert evidence_by_concept["rag_fundamentals"].score >= 0.75
    assert evidence_by_concept["retrieval_evaluation"].score < 0.45
    assert evidence_by_concept["vector_search"].score < 0.45
    assert evidence_by_concept["production_rag_failures"].score < 0.20
    assert "api_basics" in evidence_by_concept


def test_assessment_answers_are_scored_and_persisted_through_service() -> None:
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
    )

    goal = container.goal_service.create(demo.LEARNING_GOAL)
    session = agents.assessment.run_diagnostic(goal)

    recall_answer = container.assessment_service.get_answer_by_id(
        "answer_demo_recall_at_k",
    )
    assert recall_answer.assessment_session_id == session.assessment_session_id
    assert recall_answer.score == 0.25
    assert recall_answer.concept_scores[0].concept_id == "retrieval_evaluation"
    assert recall_answer.feedback == "Needs targeted practice with retrieval metrics."
