from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from app.core.settings import Settings
from app.db.mongo_client import build_mongo_client_from_settings
from app.repositories.errors import DuplicateRecordError
from app.repositories.mongo import MongoQuizRepository
from app.schemas.enums import (
    DifficultyLevel,
    QuestionType,
    QuizAttemptStatus,
    QuizStatus,
    ScoringPolicyType,
)
from app.schemas.quiz import (
    ConceptQuizScore,
    QuizAnswerSubmission,
    QuizAttemptDTO,
    QuizDTO,
    QuizQuestionDTO,
    QuizScoringPolicy,
)

ENABLE_LIVE_MONGO_TESTS = "ENABLE_LIVE_MONGO_TESTS"

pytestmark = pytest.mark.skipif(
    os.getenv(ENABLE_LIVE_MONGO_TESTS, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live MongoDB checks are optional and require "
        f"{ENABLE_LIVE_MONGO_TESTS}=1."
    ),
)


@pytest.fixture
def quiz_repository() -> Iterator[MongoQuizRepository]:
    settings = Settings()
    if not settings.mongodb_uri:
        pytest.skip("MONGODB_URI is not configured.")
    client = build_mongo_client_from_settings(settings)
    database = client[settings.mongodb_database_name]
    repository = MongoQuizRepository(
        database["test_17h_quizzes"],
        database["test_17h_quiz_attempts"],
    )
    try:
        yield repository
    finally:
        repository.clear()
        client.close()


def _sample_quiz(quiz_id: str, goal_id: str, curriculum_id: str) -> QuizDTO:
    now = datetime.now(tz=UTC)
    return QuizDTO(
        quiz_id=quiz_id,
        goal_id=goal_id,
        curriculum_id=curriculum_id,
        target_topic_ids=["topic_live17h_a"],
        target_concept_ids=["distributed_systems"],
        status=QuizStatus.ACTIVE,
        title="Live Mongo repository test quiz",
        questions=[
            QuizQuestionDTO(
                question_id="question_live17h_a",
                question_type=QuestionType.MULTIPLE_CHOICE,
                prompt="Which algorithm is used for leader election in Raft?",
                concept_ids=["distributed_systems"],
                difficulty=DifficultyLevel.INTERMEDIATE,
                correct_answer="Randomized timeout election",
                points=1.0,
                options=["Randomized timeout election", "Round robin"],
            ),
        ],
        scoring_policy=QuizScoringPolicy(type=ScoringPolicyType.EXACT_MATCH),
        created_at=now,
        updated_at=now,
    )


def _sample_attempt(
    quiz_attempt_id: str,
    quiz_id: str,
    goal_id: str,
    curriculum_id: str,
) -> QuizAttemptDTO:
    now = datetime.now(tz=UTC)
    return QuizAttemptDTO(
        quiz_attempt_id=quiz_attempt_id,
        quiz_id=quiz_id,
        goal_id=goal_id,
        curriculum_id=curriculum_id,
        answers=[
            QuizAnswerSubmission(
                question_id="question_live17h_a",
                selected_options=["Randomized timeout election"],
            ),
        ],
        total_score=1.0,
        correct_count=1,
        total_questions=1,
        concept_scores=[
            ConceptQuizScore(
                concept_id="distributed_systems",
                score=1.0,
                correct_count=1,
                total_questions=1,
            ),
        ],
        submitted_at=now,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.live_mongo
def test_quiz_create_get_and_duplicate(quiz_repository: MongoQuizRepository) -> None:
    quiz = _sample_quiz("quiz_live17h_a", "goal_live17h_a", "curriculum_live17h_a")

    created = quiz_repository.create_quiz(quiz)
    assert created.quiz_id == quiz.quiz_id

    fetched = quiz_repository.get_quiz_by_id(quiz.quiz_id)
    assert fetched == created

    with pytest.raises(DuplicateRecordError):
        quiz_repository.create_quiz(quiz)

    updated = quiz_repository.update_quiz_status(quiz.quiz_id, QuizStatus.COMPLETED)
    assert updated.status == QuizStatus.COMPLETED


@pytest.mark.live_mongo
def test_quiz_attempt_lifecycle_and_list_by_methods(
    quiz_repository: MongoQuizRepository,
) -> None:
    quiz = _sample_quiz("quiz_live17h_b", "goal_live17h_b", "curriculum_live17h_b")
    quiz_repository.create_quiz(quiz)

    attempt = _sample_attempt("attempt_live17h_b", quiz.quiz_id, quiz.goal_id, quiz.curriculum_id)
    quiz_repository.create_attempt(attempt)

    assert len(quiz_repository.list_quizzes_by_goal_id(quiz.goal_id)) == 1
    assert len(quiz_repository.list_quizzes_by_curriculum_id(quiz.curriculum_id)) == 1
    assert len(quiz_repository.list_attempts_by_quiz_id(quiz.quiz_id)) == 1
    assert len(quiz_repository.list_attempts_by_goal_id(quiz.goal_id)) == 1
    assert len(quiz_repository.list_attempts_by_curriculum_id(quiz.curriculum_id)) == 1

    updated = quiz_repository.update_attempt_status(
        attempt.quiz_attempt_id,
        QuizAttemptStatus.FAILED,
    )
    assert updated.status == QuizAttemptStatus.FAILED
