from __future__ import annotations

from typing import Any

from pymongo.collection import Collection

from app.repositories.mongo.base import MongoStore
from app.schemas.enums import GoalStatus
from app.schemas.goal import LearningGoalDTO
from app.schemas.ids import GoalId, RunId, UserId


class MongoGoalRepository:
    def __init__(self, collection: Collection[dict[str, Any]]) -> None:
        self._goals: MongoStore[LearningGoalDTO] = MongoStore(
            collection,
            LearningGoalDTO,
            "learning goal",
        )

    def create(self, goal: LearningGoalDTO) -> LearningGoalDTO:
        return self._goals.create(goal.goal_id, goal)

    def save(self, goal: LearningGoalDTO) -> LearningGoalDTO:
        return self._goals.save(goal.goal_id, goal)

    def get_by_id(self, goal_id: GoalId) -> LearningGoalDTO:
        return self._goals.get(goal_id)

    def get_by_run_id(self, run_id: RunId) -> LearningGoalDTO:
        return self._goals.get_where("run_id", run_id)

    def find_by_owner(self, owner_user_id: UserId) -> LearningGoalDTO | None:
        matches = self._goals.list_where("owner_user_id", owner_user_id)
        return matches[0] if matches else None

    def list_all(self) -> list[LearningGoalDTO]:
        return self._goals.list_all()

    def update_status(self, goal_id: GoalId, status: GoalStatus) -> LearningGoalDTO:
        return self._goals.update_fields(goal_id, status=status)

    def delete(self, goal_id: GoalId) -> None:
        self._goals.delete(goal_id)

    def clear(self) -> None:
        self._goals.clear()
