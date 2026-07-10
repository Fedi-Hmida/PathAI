from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from app.core.settings import Settings
from app.db.mongo_client import build_mongo_client_from_settings
from app.repositories.errors import DuplicateRecordError
from app.repositories.mongo import MongoAssessmentRepository
from app.schemas.assessment import AssessmentAnswerDTO, AssessmentQuestionDTO, AssessmentSessionDTO
from app.schemas.enums import AssessmentStatus, DifficultyLevel, QuestionType

ENABLE_LIVE_MONGO_TESTS = "ENABLE_LIVE_MONGO_TESTS"

pytestmark = pytest.mark.skipif(
    os.getenv(ENABLE_LIVE_MONGO_TESTS, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live MongoDB checks are optional and require "
        f"{ENABLE_LIVE_MONGO_TESTS}=1."
    ),
)


@pytest.fixture
def assessment_repository() -> Iterator[MongoAssessmentRepository]:
    settings = Settings()
    if not settings.mongodb_uri:
        pytest.skip("MONGODB_URI is not configured.")
    client = build_mongo_client_from_settings(settings)
    database = client[settings.mongodb_database_name]
    repository = MongoAssessmentRepository(
        database["test_17c_assessment_sessions"],
        database["test_17c_assessment_answers"],
    )
    try:
        yield repository
    finally:
        repository.clear()
        client.close()


def _sample_session(assessment_session_id: str, goal_id: str, run_id: str) -> AssessmentSessionDTO:
    now = datetime.now(tz=UTC)
    return AssessmentSessionDTO(
        assessment_session_id=assessment_session_id,
        goal_id=goal_id,
        run_id=run_id,
        status=AssessmentStatus.IN_PROGRESS,
        question_count=1,
        confidence=0.2,
        started_at=now,
        created_at=now,
        updated_at=now,
    )


def _sample_answer(answer_id: str, assessment_session_id: str, goal_id: str) -> AssessmentAnswerDTO:
    now = datetime.now(tz=UTC)
    return AssessmentAnswerDTO(
        answer_id=answer_id,
        assessment_session_id=assessment_session_id,
        goal_id=goal_id,
        question=AssessmentQuestionDTO(
            question_id="question_live17c_a",
            question_type=QuestionType.SHORT_ANSWER,
            prompt="What is eventual consistency?",
            target_concepts=["distributed_systems"],
            difficulty=DifficultyLevel.INTERMEDIATE,
        ),
        score=0.5,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.live_mongo
def test_assessment_session_create_get_and_duplicate(
    assessment_repository: MongoAssessmentRepository,
) -> None:
    session = _sample_session("assessment_live17c_a", "goal_live17c_a", "run_live17c_a")

    created = assessment_repository.create_session(session)
    assert created.assessment_session_id == session.assessment_session_id

    fetched = assessment_repository.get_session_by_id(session.assessment_session_id)
    assert fetched == created

    with pytest.raises(DuplicateRecordError):
        assessment_repository.create_session(session)


@pytest.mark.live_mongo
def test_assessment_answer_lifecycle_and_session_relationship(
    assessment_repository: MongoAssessmentRepository,
) -> None:
    session = _sample_session("assessment_live17c_b", "goal_live17c_b", "run_live17c_b")
    assessment_repository.create_session(session)

    answer = _sample_answer(
        "answer_live17c_b",
        session.assessment_session_id,
        session.goal_id,
    )
    assessment_repository.create_answer(answer)

    updated_session = assessment_repository.update_session_status(
        session.assessment_session_id,
        AssessmentStatus.COMPLETED,
    )
    assert updated_session.status == AssessmentStatus.COMPLETED

    by_session = assessment_repository.list_answers_by_session_id(session.assessment_session_id)
    assert len(by_session) == 1

    by_goal = assessment_repository.list_answers_by_goal_id(session.goal_id)
    assert len(by_goal) == 1

    by_run = assessment_repository.list_sessions_by_run_id(session.run_id)
    assert len(by_run) == 1
