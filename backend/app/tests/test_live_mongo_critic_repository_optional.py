from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest

from app.core.settings import Settings
from app.db.mongo_client import build_mongo_client_from_settings
from app.repositories.errors import DuplicateRecordError
from app.repositories.mongo import MongoCriticReviewRepository
from app.schemas.critic import CriticDimensionScores, CriticReviewDTO
from app.schemas.enums import CriticPassStatus

ENABLE_LIVE_MONGO_TESTS = "ENABLE_LIVE_MONGO_TESTS"

pytestmark = pytest.mark.skipif(
    os.getenv(ENABLE_LIVE_MONGO_TESTS, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live MongoDB checks are optional and require "
        f"{ENABLE_LIVE_MONGO_TESTS}=1."
    ),
)


@pytest.fixture
def critic_review_repository() -> Iterator[MongoCriticReviewRepository]:
    settings = Settings()
    if not settings.mongodb_uri:
        pytest.skip("MONGODB_URI is not configured.")
    client = build_mongo_client_from_settings(settings)
    collection = client[settings.mongodb_database_name]["test_17j_critic_reviews"]
    repository = MongoCriticReviewRepository(collection)
    try:
        yield repository
    finally:
        repository.clear()
        client.close()


def _sample_critic_review(
    critic_review_id: str,
    goal_id: str,
    curriculum_id: str,
    run_id: str,
) -> CriticReviewDTO:
    now = datetime.now(tz=UTC)
    return CriticReviewDTO(
        critic_review_id=critic_review_id,
        goal_id=goal_id,
        curriculum_id=curriculum_id,
        run_id=run_id,
        overall_score=0.75,
        pass_status=CriticPassStatus.PASS_WITH_WARNINGS,
        dimension_scores=CriticDimensionScores(
            coverage=0.8,
            pacing=0.7,
            resource_relevance=0.75,
            assessment_alignment=0.8,
        ),
        issues=["Week 3 is slightly overloaded."],
        created_at=now,
        updated_at=now,
    )


@pytest.mark.live_mongo
def test_critic_review_create_get_and_duplicate(
    critic_review_repository: MongoCriticReviewRepository,
) -> None:
    review = _sample_critic_review(
        "critic_live17j_a",
        "goal_live17j_a",
        "curriculum_live17j_a",
        "run_live17j_a",
    )

    created = critic_review_repository.create(review)
    assert created.critic_review_id == review.critic_review_id
    assert created.dimension_scores.coverage == 0.8

    fetched = critic_review_repository.get_by_id(review.critic_review_id)
    assert fetched == created

    with pytest.raises(DuplicateRecordError):
        critic_review_repository.create(review)


@pytest.mark.live_mongo
def test_critic_review_list_by_goal_run_and_curriculum_and_save(
    critic_review_repository: MongoCriticReviewRepository,
) -> None:
    review = _sample_critic_review(
        "critic_live17j_b",
        "goal_live17j_b",
        "curriculum_live17j_b",
        "run_live17j_b",
    )
    critic_review_repository.create(review)

    assert len(critic_review_repository.list_by_goal_id(review.goal_id)) == 1
    assert len(critic_review_repository.list_by_run_id(review.run_id)) == 1
    assert len(critic_review_repository.list_by_curriculum_id(review.curriculum_id)) == 1

    revised = review.model_copy(update={"pass_status": CriticPassStatus.PASS})
    saved = critic_review_repository.save(revised)
    assert saved.pass_status == CriticPassStatus.PASS
