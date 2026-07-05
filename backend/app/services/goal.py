from __future__ import annotations

from dataclasses import dataclass

from app.repositories.protocols.goal import GoalRepository
from app.schemas.enums import GoalStatus
from app.schemas.goal import LearningGoalDTO
from app.schemas.ids import GoalId, RunId


@dataclass(slots=True)
class GoalService:
    repository: GoalRepository

    def create(self, goal: LearningGoalDTO) -> LearningGoalDTO:
        return self.repository.create(goal)

    def save(self, goal: LearningGoalDTO) -> LearningGoalDTO:
        return self.repository.save(goal)

    def get_by_id(self, goal_id: GoalId) -> LearningGoalDTO:
        return self.repository.get_by_id(goal_id)

    def get_by_run_id(self, run_id: RunId) -> LearningGoalDTO:
        return self.repository.get_by_run_id(run_id)

    def list_all(self) -> list[LearningGoalDTO]:
        return self.repository.list_all()

    def update_status(self, goal_id: GoalId, status: GoalStatus) -> LearningGoalDTO:
        return self.repository.update_status(goal_id, status)
