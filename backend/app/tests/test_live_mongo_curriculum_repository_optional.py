from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from app.core.settings import Settings
from app.db.mongo_client import build_mongo_client_from_settings
from app.repositories.errors import DuplicateRecordError
from app.repositories.mongo import MongoCurriculumRepository
from app.schemas.curriculum import CurriculumDTO, CurriculumTopicDTO, CurriculumWeekDTO
from app.schemas.enums import CurriculumStatus, DifficultyLevel

ENABLE_LIVE_MONGO_TESTS = "ENABLE_LIVE_MONGO_TESTS"

pytestmark = pytest.mark.skipif(
    os.getenv(ENABLE_LIVE_MONGO_TESTS, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live MongoDB checks are optional and require "
        f"{ENABLE_LIVE_MONGO_TESTS}=1."
    ),
)


@pytest.fixture
def curriculum_repository() -> Iterator[MongoCurriculumRepository]:
    settings = Settings()
    if not settings.mongodb_uri:
        pytest.skip("MONGODB_URI is not configured.")
    client = build_mongo_client_from_settings(settings)
    collection = client[settings.mongodb_database_name]["test_17e_curricula"]
    repository = MongoCurriculumRepository(collection)
    try:
        yield repository
    finally:
        repository.clear()
        client.close()


def _sample_curriculum(
    curriculum_id: str,
    goal_id: str,
    knowledge_map_id: str,
    run_id: str,
) -> CurriculumDTO:
    now = datetime.now(tz=UTC)
    topic = CurriculumTopicDTO(
        topic_id="topic_live17e_a",
        title="Consensus Algorithms",
        description="Introduce Raft and Paxos at a high level.",
        concept_ids=["distributed_systems"],
        difficulty=DifficultyLevel.INTERMEDIATE,
        estimated_hours=3.0,
        learning_outcomes=["Explain leader election"],
        sequence_order=1,
    )
    week = CurriculumWeekDTO(
        week_id="week_live17e_a",
        week_number=1,
        theme="Consensus foundations",
        topics=[topic],
        estimated_hours=3.0,
        learning_outcomes=["Explain leader election"],
    )
    return CurriculumDTO(
        curriculum_id=curriculum_id,
        goal_id=goal_id,
        knowledge_map_id=knowledge_map_id,
        run_id=run_id,
        status=CurriculumStatus.DRAFT,
        title="Live Mongo repository test curriculum",
        duration_weeks=1,
        weeks=[week],
        target_outcomes=["Explain leader election"],
        created_at=now,
        updated_at=now,
    )


@pytest.mark.live_mongo
def test_curriculum_create_get_and_duplicate(
    curriculum_repository: MongoCurriculumRepository,
) -> None:
    curriculum = _sample_curriculum(
        "curriculum_live17e_a",
        "goal_live17e_a",
        "kmap_live17e_a",
        "run_live17e_a",
    )

    created = curriculum_repository.create(curriculum)
    assert created.curriculum_id == curriculum.curriculum_id
    assert created.weeks[0].topics[0].topic_id == "topic_live17e_a"

    fetched = curriculum_repository.get_by_id(curriculum.curriculum_id)
    assert fetched == created

    with pytest.raises(DuplicateRecordError):
        curriculum_repository.create(curriculum)


@pytest.mark.live_mongo
def test_curriculum_list_by_goal_run_and_knowledge_map_and_update_status(
    curriculum_repository: MongoCurriculumRepository,
) -> None:
    curriculum = _sample_curriculum(
        "curriculum_live17e_b",
        "goal_live17e_b",
        "kmap_live17e_b",
        "run_live17e_b",
    )
    curriculum_repository.create(curriculum)

    assert len(curriculum_repository.list_by_goal_id(curriculum.goal_id)) == 1
    assert len(curriculum_repository.list_by_run_id(curriculum.run_id)) == 1
    assert len(curriculum_repository.list_by_knowledge_map_id(curriculum.knowledge_map_id)) == 1

    updated = curriculum_repository.update_status(
        curriculum.curriculum_id,
        CurriculumStatus.ACTIVE,
    )
    assert updated.status == CurriculumStatus.ACTIVE
