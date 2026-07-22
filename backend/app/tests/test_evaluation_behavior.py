from __future__ import annotations

import re

from app.agents.mock import MockEvaluationAgent
from app.agents.services.evaluation import EvaluationAgentService
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.assessment import AssessmentSessionDTO, ConceptEvidence
from app.schemas.critic import CriticDimensionScores, CriticReviewDTO
from app.schemas.curriculum import CurriculumDTO, CurriculumTopicDTO, CurriculumWeekDTO
from app.schemas.enums import (
    AssessmentStatus,
    ConceptClassification,
    CriticPassStatus,
    CurriculumStatus,
    DifficultyLevel,
    GoalStatus,
    KnowledgeMapStatus,
)
from app.schemas.evaluation import EvaluationAgentInput, EvaluationAgentOutput
from app.schemas.goal import LearnerProfile, LearningGoalDTO
from app.schemas.knowledge_map import ConceptMasteryDTO, KnowledgeMapDTO
from app.schemas.quiz import ConceptQuizScore, QuizAnswerSubmission, QuizAttemptDTO

_RAG_TOKEN_PATTERN = re.compile(
    r"\b(rag|retrieval|reranking|chunking|embeddings?|vector[_ ]search|hallucination)\b",
    re.IGNORECASE,
)


def _assert_no_rag_vocabulary(*fragments: str) -> None:
    blob = " ".join(fragments)
    match = _RAG_TOKEN_PATTERN.search(blob)
    assert match is None, f"RAG vocabulary leaked into non-RAG evaluation output: {match!r}"


def test_evaluation_agent_calculates_metrics_from_artifacts() -> None:
    output = MockEvaluationAgent().evaluate_run(_evaluation_input())

    assert EvaluationAgentOutput.model_validate(output) == output
    assert output.metric_scores.workflow_completeness == 1.0
    assert output.metric_scores.resource_diversity == 0.4
    assert output.metric_scores.resource_relevance == 0.93
    assert output.metric_scores.quiz_alignment >= 0.75
    assert output.metric_scores.adaptation_usefulness is not None
    assert output.weighted_score >= 0.7
    assert "Resource diversity" in " ".join(output.warnings)


def test_evaluation_agent_service_persists_calculated_report() -> None:
    container = ApiServiceContainer()
    service = EvaluationAgentService(MockEvaluationAgent(), container.evaluation_service)

    report = service.evaluate(
        demo.LEARNING_GOAL,
        demo.ASSESSMENT_SESSION,
        demo.KNOWLEDGE_MAP,
        demo.CURRICULUM,
        demo.RESOURCE_ATTACHMENTS,
        demo.CRITIC_REVIEW,
        demo.QUIZ_ATTEMPT,
        demo.ADAPTATION_EVENT,
    )

    stored = container.evaluation_service.get_by_id(report.evaluation_report_id)
    assert stored == report
    assert report.artifact_ids["goal_id"] == demo.GOAL_ID
    assert report.artifact_ids["quiz_attempt_id"] == demo.QUIZ_ATTEMPT_ID
    assert report.weights["workflow_completeness"] > 0
    assert report.overall_score == report.model_copy().overall_score


def test_evaluation_for_a_non_rag_goal_contains_no_rag_content() -> None:
    output = MockEvaluationAgent().evaluate_run(_non_rag_evaluation_input())

    assert EvaluationAgentOutput.model_validate(output) == output
    blob = output.model_dump_json().lower()
    _assert_no_rag_vocabulary(blob)
    # The deterministic agent interpolates quiz_attempt.weak_concepts verbatim
    # into a recommendation string - proving that echo is genuinely about the
    # real (non-RAG) input, not just empty of RAG terms by accident.
    assert "finger picking" in blob


def _non_rag_evaluation_input() -> EvaluationAgentInput:
    goal = LearningGoalDTO(
        goal_id="goal_guitar",
        run_id="run_guitar",
        goal_text="Learn classical guitar for a wedding performance",
        normalized_goal_text="learn classical guitar for a wedding performance",
        status=GoalStatus.CURRICULUM_GENERATED,
        learner_profile=LearnerProfile(
            learner_type="adult_hobbyist",
            time_availability_hours_per_week=5,
            desired_outcome="Perform a short classical guitar set at a wedding.",
            difficulty_target=DifficultyLevel.INTERMEDIATE,
        ),
        hours_per_week=5,
        target_duration_weeks=2,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )
    assessment = AssessmentSessionDTO(
        assessment_session_id="assessment_guitar",
        goal_id="goal_guitar",
        run_id="run_guitar",
        status=AssessmentStatus.COMPLETED,
        question_count=3,
        confidence=0.7,
        concept_evidence=[
            ConceptEvidence(
                concept_id="finger_picking_technique",
                score=0.3,
                evidence=["Struggled with basic finger-picking transitions."],
            ),
        ],
        started_at=demo.NOW,
        completed_at=demo.NOW,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )
    knowledge_map = KnowledgeMapDTO(
        knowledge_map_id="kmap_guitar",
        goal_id="goal_guitar",
        assessment_session_id="assessment_guitar",
        run_id="run_guitar",
        status=KnowledgeMapStatus.ACTIVE,
        concepts=[
            ConceptMasteryDTO(
                concept_id="music_theory_basics",
                label="Music theory basics",
                mastery_score=0.8,
                classification=ConceptClassification.STRONG,
            ),
            ConceptMasteryDTO(
                concept_id="finger_picking_technique",
                label="Finger-picking technique",
                mastery_score=0.3,
                classification=ConceptClassification.WEAK,
                prerequisites=["music_theory_basics"],
            ),
            ConceptMasteryDTO(
                concept_id="wedding_repertoire",
                label="Wedding repertoire",
                mastery_score=0.1,
                classification=ConceptClassification.MISSING,
                prerequisites=["finger_picking_technique"],
            ),
        ],
        strong_concepts=["music_theory_basics"],
        weak_concepts=["finger_picking_technique"],
        missing_concepts=["wedding_repertoire"],
        confidence=0.7,
        summary="Strong on theory, needs finger-picking and repertoire work.",
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )
    curriculum = CurriculumDTO(
        curriculum_id="curriculum_guitar",
        goal_id="goal_guitar",
        knowledge_map_id="kmap_guitar",
        run_id="run_guitar",
        status=CurriculumStatus.ACTIVE,
        title="Classical Guitar for a Wedding Performance",
        duration_weeks=2,
        target_outcomes=["Perform a short classical guitar set at a wedding."],
        created_at=demo.NOW,
        updated_at=demo.NOW,
        weeks=[
            CurriculumWeekDTO(
                week_id="week_intro",
                week_number=1,
                theme="Foundations",
                estimated_hours=5.0,
                learning_outcomes=["Read basic notation and rhythm."],
                topics=[
                    CurriculumTopicDTO(
                        topic_id="topic_theory",
                        title="Music theory basics",
                        description="Notation, rhythm, and key signatures.",
                        concept_ids=["music_theory_basics"],
                        difficulty=DifficultyLevel.BEGINNER,
                        estimated_hours=5.0,
                        learning_outcomes=["Read basic notation."],
                        sequence_order=1,
                    ),
                ],
            ),
            CurriculumWeekDTO(
                week_id="week_repertoire",
                week_number=2,
                theme="Performance repertoire",
                estimated_hours=5.0,
                learning_outcomes=["Play a wedding-appropriate piece."],
                topics=[
                    CurriculumTopicDTO(
                        topic_id="topic_repertoire",
                        title="Wedding repertoire",
                        description="Learn a short classical piece for the ceremony.",
                        concept_ids=["wedding_repertoire", "finger_picking_technique"],
                        difficulty=DifficultyLevel.INTERMEDIATE,
                        estimated_hours=5.0,
                        learning_outcomes=["Perform a full piece from memory."],
                        sequence_order=2,
                    ),
                ],
            ),
        ],
    )
    critic_review = CriticReviewDTO(
        critic_review_id="critic_guitar",
        goal_id="goal_guitar",
        curriculum_id="curriculum_guitar",
        run_id="run_guitar",
        overall_score=0.82,
        pass_status=CriticPassStatus.PASS_WITH_WARNINGS,
        dimension_scores=CriticDimensionScores(
            coverage=0.85,
            pacing=0.8,
            resource_relevance=0.75,
            assessment_alignment=0.8,
            quiz_readiness=0.8,
        ),
        strengths=["Strong coverage of wedding repertoire fundamentals."],
        issues=["Weak coverage: finger-picking technique needs more practice time."],
        revision_recommendations=[
            "Add a dedicated finger-picking practice topic before the repertoire week.",
        ],
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )
    quiz_attempt = QuizAttemptDTO(
        quiz_attempt_id="attempt_guitar",
        quiz_id="quiz_guitar",
        goal_id="goal_guitar",
        curriculum_id="curriculum_guitar",
        answers=[
            QuizAnswerSubmission(question_id="question_fingerpicking", selected_options=["A"]),
        ],
        total_score=0.6,
        correct_count=3,
        total_questions=5,
        concept_scores=[
            ConceptQuizScore(
                concept_id="finger_picking_technique",
                score=0.4,
                correct_count=2,
                total_questions=5,
            ),
        ],
        weak_concepts=["finger_picking_technique"],
        submitted_at=demo.NOW,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )
    return EvaluationAgentInput(
        goal=goal,
        assessment=assessment,
        knowledge_map=knowledge_map,
        curriculum=curriculum,
        resources=[],
        critic_review=critic_review,
        quiz_attempt=quiz_attempt,
        adaptation_event=None,
    )


def _evaluation_input() -> EvaluationAgentInput:
    return EvaluationAgentInput(
        goal=demo.LEARNING_GOAL,
        assessment=demo.ASSESSMENT_SESSION,
        knowledge_map=demo.KNOWLEDGE_MAP,
        curriculum=demo.CURRICULUM,
        resources=demo.RESOURCE_ATTACHMENTS,
        critic_review=demo.CRITIC_REVIEW,
        quiz_attempt=demo.QUIZ_ATTEMPT,
        adaptation_event=demo.ADAPTATION_EVENT,
    )
