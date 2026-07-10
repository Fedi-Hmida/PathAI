from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from app.core.settings import Settings
from app.db.mongo_client import build_mongo_client_from_settings
from app.repositories.errors import DuplicateRecordError
from app.repositories.mongo import MongoKnowledgeMapRepository
from app.schemas.enums import ConceptClassification, KnowledgeMapStatus
from app.schemas.knowledge_map import ConceptMasteryDTO, KnowledgeMapDTO

ENABLE_LIVE_MONGO_TESTS = "ENABLE_LIVE_MONGO_TESTS"

pytestmark = pytest.mark.skipif(
    os.getenv(ENABLE_LIVE_MONGO_TESTS, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live MongoDB checks are optional and require "
        f"{ENABLE_LIVE_MONGO_TESTS}=1."
    ),
)


@pytest.fixture
def knowledge_map_repository() -> Iterator[MongoKnowledgeMapRepository]:
    settings = Settings()
    if not settings.mongodb_uri:
        pytest.skip("MONGODB_URI is not configured.")
    client = build_mongo_client_from_settings(settings)
    collection = client[settings.mongodb_database_name]["test_17d_knowledge_maps"]
    repository = MongoKnowledgeMapRepository(collection)
    try:
        yield repository
    finally:
        repository.clear()
        client.close()


def _sample_knowledge_map(
    knowledge_map_id: str,
    goal_id: str,
    assessment_session_id: str,
    run_id: str,
) -> KnowledgeMapDTO:
    now = datetime.now(tz=UTC)
    return KnowledgeMapDTO(
        knowledge_map_id=knowledge_map_id,
        goal_id=goal_id,
        assessment_session_id=assessment_session_id,
        run_id=run_id,
        status=KnowledgeMapStatus.DRAFT,
        concepts=[
            ConceptMasteryDTO(
                concept_id="distributed_systems",
                label="Distributed Systems",
                mastery_score=0.4,
                classification=ConceptClassification.DEVELOPING,
            ),
        ],
        developing_concepts=["distributed_systems"],
        confidence=0.5,
        summary="Live Mongo repository test knowledge map.",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.live_mongo
def test_knowledge_map_create_get_and_duplicate(
    knowledge_map_repository: MongoKnowledgeMapRepository,
) -> None:
    knowledge_map = _sample_knowledge_map(
        "kmap_live17d_a",
        "goal_live17d_a",
        "assessment_live17d_a",
        "run_live17d_a",
    )

    created = knowledge_map_repository.create(knowledge_map)
    assert created.knowledge_map_id == knowledge_map.knowledge_map_id
    assert created.concepts[0].concept_id == "distributed_systems"

    fetched = knowledge_map_repository.get_by_id(knowledge_map.knowledge_map_id)
    assert fetched == created

    with pytest.raises(DuplicateRecordError):
        knowledge_map_repository.create(knowledge_map)


@pytest.mark.live_mongo
def test_knowledge_map_list_by_goal_and_run_and_update_status(
    knowledge_map_repository: MongoKnowledgeMapRepository,
) -> None:
    knowledge_map = _sample_knowledge_map(
        "kmap_live17d_b",
        "goal_live17d_b",
        "assessment_live17d_b",
        "run_live17d_b",
    )
    knowledge_map_repository.create(knowledge_map)

    by_goal = knowledge_map_repository.list_by_goal_id(knowledge_map.goal_id)
    assert len(by_goal) == 1

    by_run = knowledge_map_repository.list_by_run_id(knowledge_map.run_id)
    assert len(by_run) == 1

    updated = knowledge_map_repository.update_status(
        knowledge_map.knowledge_map_id,
        KnowledgeMapStatus.ACTIVE,
    )
    assert updated.status == KnowledgeMapStatus.ACTIVE
