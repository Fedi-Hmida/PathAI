from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from app.core.settings import Settings
from app.db.mongo_client import build_mongo_client_from_settings
from app.repositories.errors import DuplicateRecordError
from app.repositories.mongo import MongoProgressRepository
from app.schemas.enums import ProgressStatus, TopicProgressStatus
from app.schemas.progress import ProgressStateDTO, TopicProgressDTO

ENABLE_LIVE_MONGO_TESTS = "ENABLE_LIVE_MONGO_TESTS"

pytestmark = pytest.mark.skipif(
    os.getenv(ENABLE_LIVE_MONGO_TESTS, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live MongoDB checks are optional and require "
        f"{ENABLE_LIVE_MONGO_TESTS}=1."
    ),
)


@pytest.fixture
def progress_repository() -> Iterator[MongoProgressRepository]:
    settings = Settings()
    if not settings.mongodb_uri:
        pytest.skip("MONGODB_URI is not configured.")
    client = build_mongo_client_from_settings(settings)
    collection = client[settings.mongodb_database_name]["test_17g_progress_states"]
    repository = MongoProgressRepository(collection)
    try:
        yield repository
    finally:
        repository.clear()
        client.close()


def _sample_progress_state(
    progress_state_id: str,
    goal_id: str,
    curriculum_id: str,
) -> ProgressStateDTO:
    now = datetime.now(tz=UTC)
    return ProgressStateDTO(
        progress_state_id=progress_state_id,
        goal_id=goal_id,
        curriculum_id=curriculum_id,
        status=ProgressStatus.IN_PROGRESS,
        overall_completion=0.2,
        topic_progress=[
            TopicProgressDTO(
                topic_id="topic_live17g_a",
                status=TopicProgressStatus.IN_PROGRESS,
                completion=0.2,
            ),
        ],
        created_at=now,
        updated_at=now,
    )


@pytest.mark.live_mongo
def test_progress_state_create_get_and_duplicate(
    progress_repository: MongoProgressRepository,
) -> None:
    progress_state = _sample_progress_state(
        "progress_live17g_a",
        "goal_live17g_a",
        "curriculum_live17g_a",
    )

    created = progress_repository.create(progress_state)
    assert created.progress_state_id == progress_state.progress_state_id
    assert created.topic_progress[0].topic_id == "topic_live17g_a"

    fetched = progress_repository.get_by_id(progress_state.progress_state_id)
    assert fetched == created

    with pytest.raises(DuplicateRecordError):
        progress_repository.create(progress_state)


@pytest.mark.live_mongo
def test_progress_state_list_by_goal_and_curriculum_and_update_status(
    progress_repository: MongoProgressRepository,
) -> None:
    progress_state = _sample_progress_state(
        "progress_live17g_b",
        "goal_live17g_b",
        "curriculum_live17g_b",
    )
    progress_repository.create(progress_state)

    assert len(progress_repository.list_by_goal_id(progress_state.goal_id)) == 1
    assert len(progress_repository.list_by_curriculum_id(progress_state.curriculum_id)) == 1

    updated = progress_repository.update_status(
        progress_state.progress_state_id,
        ProgressStatus.COMPLETED,
    )
    assert updated.status == ProgressStatus.COMPLETED
