from __future__ import annotations

from app.repositories.fakes.base import InMemoryStore
from app.schemas.enums import ProgressStatus
from app.schemas.ids import CurriculumId, GoalId, ProgressId
from app.schemas.progress import ProgressStateDTO


class FakeProgressRepository:
    def __init__(self) -> None:
        self._progress_states: InMemoryStore[ProgressStateDTO] = InMemoryStore("progress state")

    def create(self, progress_state: ProgressStateDTO) -> ProgressStateDTO:
        return self._progress_states.create(progress_state.progress_state_id, progress_state)

    def save(self, progress_state: ProgressStateDTO) -> ProgressStateDTO:
        return self._progress_states.save(progress_state.progress_state_id, progress_state)

    def get_by_id(self, progress_state_id: ProgressId) -> ProgressStateDTO:
        return self._progress_states.get(progress_state_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[ProgressStateDTO]:
        return self._progress_states.list_where("goal_id", goal_id)

    def list_by_curriculum_id(self, curriculum_id: CurriculumId) -> list[ProgressStateDTO]:
        return self._progress_states.list_where("curriculum_id", curriculum_id)

    def update_status(
        self,
        progress_state_id: ProgressId,
        status: ProgressStatus,
    ) -> ProgressStateDTO:
        return self._progress_states.update_fields(progress_state_id, status=status)

    def clear(self) -> None:
        self._progress_states.clear()
