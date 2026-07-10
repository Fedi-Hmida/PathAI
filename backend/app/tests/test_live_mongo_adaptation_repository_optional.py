from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from app.core.settings import Settings
from app.db.mongo_client import build_mongo_client_from_settings
from app.repositories.errors import DuplicateRecordError
from app.repositories.mongo import MongoAdaptationRepository
from app.schemas.adaptation import AdaptationEventDTO
from app.schemas.curriculum import CurriculumChangeDTO
from app.schemas.enums import AdaptationStatus, AdaptationTriggerType, CurriculumChangeType

ENABLE_LIVE_MONGO_TESTS = "ENABLE_LIVE_MONGO_TESTS"

pytestmark = pytest.mark.skipif(
    os.getenv(ENABLE_LIVE_MONGO_TESTS, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live MongoDB checks are optional and require "
        f"{ENABLE_LIVE_MONGO_TESTS}=1."
    ),
)


@pytest.fixture
def adaptation_repository() -> Iterator[MongoAdaptationRepository]:
    settings = Settings()
    if not settings.mongodb_uri:
        pytest.skip("MONGODB_URI is not configured.")
    client = build_mongo_client_from_settings(settings)
    collection = client[settings.mongodb_database_name]["test_17i_adaptation_events"]
    repository = MongoAdaptationRepository(collection)
    try:
        yield repository
    finally:
        repository.clear()
        client.close()


def _sample_adaptation_event(
    adaptation_event_id: str,
    goal_id: str,
    curriculum_id: str,
    quiz_attempt_id: str,
) -> AdaptationEventDTO:
    now = datetime.now(tz=UTC)
    return AdaptationEventDTO(
        adaptation_event_id=adaptation_event_id,
        goal_id=goal_id,
        curriculum_id=curriculum_id,
        trigger_type=AdaptationTriggerType.QUIZ_SCORE_BELOW_THRESHOLD,
        before_summary="Learner struggled with consensus algorithms.",
        after_summary="Added an extra practice topic on leader election.",
        changes=[
            CurriculumChangeDTO(
                change_type=CurriculumChangeType.ADD_PRACTICE_EXERCISE,
                target_week=1,
                reason="Quiz score below threshold on consensus concepts.",
            ),
        ],
        status=AdaptationStatus.PROPOSED,
        quiz_attempt_id=quiz_attempt_id,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.live_mongo
def test_adaptation_event_create_get_and_duplicate(
    adaptation_repository: MongoAdaptationRepository,
) -> None:
    event = _sample_adaptation_event(
        "adapt_live17i_a",
        "goal_live17i_a",
        "curriculum_live17i_a",
        "attempt_live17i_a",
    )

    created = adaptation_repository.create(event)
    assert created.adaptation_event_id == event.adaptation_event_id
    assert created.changes[0].change_type == CurriculumChangeType.ADD_PRACTICE_EXERCISE

    fetched = adaptation_repository.get_by_id(event.adaptation_event_id)
    assert fetched == created

    with pytest.raises(DuplicateRecordError):
        adaptation_repository.create(event)


@pytest.mark.live_mongo
def test_adaptation_event_list_by_goal_curriculum_quiz_attempt_and_update_status(
    adaptation_repository: MongoAdaptationRepository,
) -> None:
    event = _sample_adaptation_event(
        "adapt_live17i_b",
        "goal_live17i_b",
        "curriculum_live17i_b",
        "attempt_live17i_b",
    )
    adaptation_repository.create(event)

    assert len(adaptation_repository.list_by_goal_id(event.goal_id)) == 1
    assert len(adaptation_repository.list_by_curriculum_id(event.curriculum_id)) == 1
    assert event.quiz_attempt_id is not None
    assert len(adaptation_repository.list_by_quiz_attempt_id(event.quiz_attempt_id)) == 1

    updated = adaptation_repository.update_status(
        event.adaptation_event_id,
        AdaptationStatus.APPLIED,
    )
    assert updated.status == AdaptationStatus.APPLIED
