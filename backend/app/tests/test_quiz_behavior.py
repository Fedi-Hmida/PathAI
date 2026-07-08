from __future__ import annotations

from app.agents.mock import MockQuizAgent
from app.agents.services.quiz import QuizAgentService
from app.api.v1.dependencies import ApiServiceContainer
from app.api.v1.quiz import _to_learner_quiz
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumDTO, CurriculumTopicDTO
from app.schemas.enums import DifficultyLevel
from app.schemas.quiz import (
    QuizAgentInput,
    QuizAgentOutput,
    QuizAttemptDTO,
    QuizDTO,
    QuizScoreOutput,
)


def test_quiz_generation_targets_weak_and_checkpoint_concepts() -> None:
    output = _build_quiz_output(
        [
            "retrieval_evaluation",
            "vector_search",
            "chunking",
            "reranking",
            "production_rag_failures",
        ],
    )
    question_ids = [question.question_id for question in output.questions]
    concept_ids = {concept for question in output.questions for concept in question.concept_ids}

    assert QuizAgentOutput.model_validate(output) == output
    assert question_ids == [
        "question_quiz_recall_k",
        "question_quiz_vector_search",
        "question_quiz_chunking",
        "question_quiz_reranking",
        "question_quiz_production_failures",
    ]
    assert {
        "retrieval_evaluation",
        "vector_search",
        "chunking",
        "reranking",
        "production_rag_failures",
    } <= concept_ids


def test_quiz_scoring_is_deterministic_and_sets_feedback_signals() -> None:
    quiz, attempt = _build_persisted_quiz_and_attempt()
    score_output = QuizScoreOutput(
        total_score=attempt.total_score,
        correct_count=attempt.correct_count,
        total_questions=attempt.total_questions,
        concept_scores=attempt.concept_scores,
        weak_concepts=attempt.weak_concepts,
        feedback=attempt.feedback or "",
    )

    assert score_output.total_score < 0.65
    assert attempt.adaptation_triggered is True
    assert "retrieval_evaluation" in attempt.weak_concepts
    assert "vector_search" in attempt.weak_concepts
    assert "Review these concepts" in (attempt.feedback or "")
    assert len(attempt.answers) == len(quiz.questions)


def test_learner_quiz_output_does_not_expose_answer_keys() -> None:
    quiz, _attempt = _build_persisted_quiz_and_attempt()
    learner_quiz = _to_learner_quiz(quiz)
    payload = learner_quiz.model_dump()

    assert payload["quiz_id"] == demo.QUIZ_ID
    assert "correct_answer" not in str(payload)
    assert "explanation" not in str(payload)


def _build_quiz_output(target_concepts: list[str]) -> QuizAgentOutput:
    return MockQuizAgent().build_quiz(
        QuizAgentInput(
            goal_text=demo.CANONICAL_GOAL_TEXT,
            curriculum_topics=_topics(demo.CURRICULUM),
            target_concepts=target_concepts,
            difficulty=DifficultyLevel.INTERMEDIATE,
            question_count=len(target_concepts),
        ),
    )


def _build_persisted_quiz_and_attempt() -> tuple[QuizDTO, QuizAttemptDTO]:
    container = ApiServiceContainer()
    service = QuizAgentService(MockQuizAgent(), container.quiz_service)
    goal = container.goal_service.create(demo.LEARNING_GOAL)
    curriculum = container.curriculum_service.create(demo.CURRICULUM)
    progress = container.progress_service.create(demo.PROGRESS_STATE)
    return service.build(goal, curriculum, progress)


def _topics(curriculum: CurriculumDTO) -> list[CurriculumTopicDTO]:
    return [topic for week in curriculum.weeks for topic in week.topics]
