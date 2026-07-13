from __future__ import annotations

from app.agents.deterministic.assessment import (
    CANONICAL_DIAGNOSTIC_CONCEPTS,
    diagnostic_focus_for_goal,
)
from app.agents.services import build_mock_agent_service_bundle
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.enums import AssessmentStatus, DifficultyLevel
from app.schemas.goal import LearnerProfile


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


def _neutral_profile(**overrides: object) -> LearnerProfile:
    base = {
        "learner_type": "learner",
        "strengths": [],
        "weak_areas": [],
        "time_availability_hours_per_week": 5,
        "desired_outcome": "Make progress.",
        "preferred_resource_types": [],
        "difficulty_target": DifficultyLevel.INTERMEDIATE,
    }
    base.update(overrides)
    return LearnerProfile(**base)


def test_diagnostic_focus_for_a_non_rag_goal_never_defaults_to_rag() -> None:
    concepts = diagnostic_focus_for_goal(
        "Learn classical guitar for a wedding performance",
        _neutral_profile(),
    )

    assert set(concepts).isdisjoint(CANONICAL_DIAGNOSTIC_CONCEPTS)
    assert any("guitar" in concept or "wedding" in concept for concept in concepts)


def test_diagnostic_focus_matches_rag_only_on_word_boundary_not_substring() -> None:
    # "mortgage" contains "rag" as a raw substring - must not false-positive.
    concepts = diagnostic_focus_for_goal(
        "Learn how to manage a mortgage",
        _neutral_profile(),
    )

    assert set(concepts).isdisjoint(CANONICAL_DIAGNOSTIC_CONCEPTS)


def test_diagnostic_focus_for_a_genuine_rag_goal_still_uses_rag_concepts() -> None:
    concepts = diagnostic_focus_for_goal(demo.CANONICAL_GOAL_TEXT, demo.LEARNER_PROFILE)

    assert set(CANONICAL_DIAGNOSTIC_CONCEPTS) <= set(concepts)


def test_diagnostic_focus_ignores_leftover_demo_weak_areas_substring_match() -> None:
    # A profile carrying "retrieval_evaluation" as a weak area must not make
    # an unrelated goal match "retrieval" via raw substring containment.
    concepts = diagnostic_focus_for_goal(
        "Learn classical guitar for a wedding performance",
        _neutral_profile(weak_areas=["retrieval_evaluation"]),
    )

    assert "rag_fundamentals" not in concepts
