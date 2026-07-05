from __future__ import annotations

from typing import Protocol

from app.schemas.enums import ProgressStatus
from app.schemas.ids import CurriculumId, GoalId, ProgressId
from app.schemas.progress import ProgressStateDTO


class ProgressRepository(Protocol):
    def create(self, progress_state: ProgressStateDTO) -> ProgressStateDTO: ...

    def save(self, progress_state: ProgressStateDTO) -> ProgressStateDTO: ...

    def get_by_id(self, progress_state_id: ProgressId) -> ProgressStateDTO: ...

    def list_by_goal_id(self, goal_id: GoalId) -> list[ProgressStateDTO]: ...

    def list_by_curriculum_id(self, curriculum_id: CurriculumId) -> list[ProgressStateDTO]: ...

    def update_status(
        self,
        progress_state_id: ProgressId,
        status: ProgressStatus,
    ) -> ProgressStateDTO: ...

    def clear(self) -> None: ...
