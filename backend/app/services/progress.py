from __future__ import annotations

from dataclasses import dataclass

from app.repositories.protocols.progress import ProgressRepository
from app.schemas.enums import ProgressStatus
from app.schemas.ids import CurriculumId, GoalId, ProgressId
from app.schemas.progress import ProgressStateDTO


@dataclass(slots=True)
class ProgressService:
    repository: ProgressRepository

    def create(self, progress_state: ProgressStateDTO) -> ProgressStateDTO:
        return self.repository.create(progress_state)

    def save(self, progress_state: ProgressStateDTO) -> ProgressStateDTO:
        return self.repository.save(progress_state)

    def get_by_id(self, progress_state_id: ProgressId) -> ProgressStateDTO:
        return self.repository.get_by_id(progress_state_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[ProgressStateDTO]:
        return self.repository.list_by_goal_id(goal_id)

    def list_by_curriculum_id(self, curriculum_id: CurriculumId) -> list[ProgressStateDTO]:
        return self.repository.list_by_curriculum_id(curriculum_id)

    def update_status(
        self,
        progress_state_id: ProgressId,
        status: ProgressStatus,
    ) -> ProgressStateDTO:
        return self.repository.update_status(progress_state_id, status)
