from __future__ import annotations

from typing import Any

from pymongo.collection import Collection

from app.repositories.mongo.base import MongoStore
from app.schemas.critic import CriticReviewDTO
from app.schemas.ids import CriticReviewId, CurriculumId, GoalId, RunId


class MongoCriticReviewRepository:
    def __init__(self, collection: Collection[dict[str, Any]]) -> None:
        self._critic_reviews: MongoStore[CriticReviewDTO] = MongoStore(
            collection,
            CriticReviewDTO,
            "critic review",
        )

    def create(self, critic_review: CriticReviewDTO) -> CriticReviewDTO:
        return self._critic_reviews.create(critic_review.critic_review_id, critic_review)

    def save(self, critic_review: CriticReviewDTO) -> CriticReviewDTO:
        return self._critic_reviews.save(critic_review.critic_review_id, critic_review)

    def get_by_id(self, critic_review_id: CriticReviewId) -> CriticReviewDTO:
        return self._critic_reviews.get(critic_review_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[CriticReviewDTO]:
        return self._critic_reviews.list_where("goal_id", goal_id)

    def list_by_run_id(self, run_id: RunId) -> list[CriticReviewDTO]:
        return self._critic_reviews.list_where("run_id", run_id)

    def list_by_curriculum_id(self, curriculum_id: CurriculumId) -> list[CriticReviewDTO]:
        return self._critic_reviews.list_where("curriculum_id", curriculum_id)

    def clear(self) -> None:
        self._critic_reviews.clear()
