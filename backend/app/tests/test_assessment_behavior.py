from __future__ import annotations

import re

from app.agents.deterministic.assessment import (
    CANONICAL_DIAGNOSTIC_CONCEPTS,
    diagnostic_focus_for_goal,
)
from app.agents.services import build_mock_agent_service_bundle
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.assessment import AssessmentAnswerCreate
from app.schemas.enums import AssessmentStatus, DifficultyLevel
from app.schemas.goal import LearnerProfile

_RAG_TOKEN_PATTERN = re.compile(
    r"\b(rag|retrieval|reranking|chunking|embeddings?|vector[_ ]search|hallucination)\b",
    re.IGNORECASE,
)


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
    assert session.question_count == 5
    assert session.confidence >= 0.75
    assert session.termination_reason == "confidence_target_met"
    # The first 5 of the demo goal's goal-aware target concepts (RAG concepts,
    # then the profile's weak areas/strengths, deduplicated) each get one
    # self-rating question - no repeats among them.
    assert [answer.question.target_concepts[0] for answer in answers] == [
        "rag_fundamentals",
        "retrieval_evaluation",
        "vector_search",
        "chunking",
        "embeddings",
    ]

    evidence_by_concept = {
        evidence.concept_id: evidence
        for evidence in session.concept_evidence
    }
    # weak_areas (vector_search/chunking/retrieval_evaluation) seed a low
    # self-rating; concepts absent from the profile seed a neutral rating.
    assert evidence_by_concept["retrieval_evaluation"].score < 0.45
    assert evidence_by_concept["vector_search"].score < 0.45
    assert evidence_by_concept["chunking"].score < 0.45
    assert evidence_by_concept["rag_fundamentals"].score == 0.5
    # Strengths never get asked about directly but still contribute evidence.
    assert evidence_by_concept["api_basics"].score >= 0.75


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
    answers = container.assessment_service.list_answers_by_session_id(
        session.assessment_session_id,
    )

    weak_area_answer = next(
        answer for answer in answers
        if answer.question.target_concepts == ["retrieval_evaluation"]
    )
    assert weak_area_answer.assessment_session_id == session.assessment_session_id
    assert weak_area_answer.self_rating == 2
    assert weak_area_answer.score == 0.25
    assert weak_area_answer.concept_scores[0].concept_id == "retrieval_evaluation"
    assert weak_area_answer.feedback == "Add targeted practice before moving deeper."


def test_full_turn_by_turn_diagnostic_for_a_non_rag_goal_contains_no_rag_vocabulary() -> None:
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
    goal_text = "Learn classical guitar for a wedding performance"
    goal = container.goal_service.create(
        demo.LEARNING_GOAL.model_copy(
            update={
                "goal_text": goal_text,
                "normalized_goal_text": goal_text,
                "learner_profile": _neutral_profile(),
            },
            deep=True,
        ),
    )

    session = agents.assessment.start(goal)
    seen_prompts: list[str] = []
    for rating in (2, 4, 3, 5, 1):
        assert session.current_question is not None
        question = session.current_question
        seen_prompts.append(question.prompt)
        answer_create = AssessmentAnswerCreate(
            question_id=question.question_id,
            self_rating=rating,
        )
        session, _ = agents.assessment.submit_answer(
            goal=goal,
            session=session,
            answer_create=answer_create,
        )

    assert session.status == AssessmentStatus.COMPLETED
    assert session.question_count == 5

    serialized_prompts = " ".join(seen_prompts)
    assert not _RAG_TOKEN_PATTERN.search(serialized_prompts), serialized_prompts
    assert session.concept_evidence
    for evidence in session.concept_evidence:
        assert not _RAG_TOKEN_PATTERN.search(evidence.concept_id), evidence.concept_id


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
