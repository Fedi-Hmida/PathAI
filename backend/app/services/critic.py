from __future__ import annotations

from dataclasses import dataclass

from app.repositories.protocols.critic import CriticReviewRepository
from app.schemas.critic import CriticReviewDTO
from app.schemas.ids import CriticReviewId, CurriculumId, GoalId, RunId


@dataclass(slots=True)
class CriticService:
    repository: CriticReviewRepository

    def create(self, critic_review: CriticReviewDTO) -> CriticReviewDTO:
        return self.repository.create(critic_review)

    def save(self, critic_review: CriticReviewDTO) -> CriticReviewDTO:
        return self.repository.save(critic_review)

    def get_by_id(self, critic_review_id: CriticReviewId) -> CriticReviewDTO:
        return self.repository.get_by_id(critic_review_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[CriticReviewDTO]:
        return self.repository.list_by_goal_id(goal_id)

    def list_by_run_id(self, run_id: RunId) -> list[CriticReviewDTO]:
        return self.repository.list_by_run_id(run_id)

    def list_by_curriculum_id(self, curriculum_id: CurriculumId) -> list[CriticReviewDTO]:
        return self.repository.list_by_curriculum_id(curriculum_id)
