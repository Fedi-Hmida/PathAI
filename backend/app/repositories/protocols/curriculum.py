from __future__ import annotations

from typing import Protocol

from app.schemas.curriculum import CurriculumDTO
from app.schemas.enums import CurriculumStatus
from app.schemas.ids import CurriculumId, GoalId, KnowledgeMapId, RunId


class CurriculumRepository(Protocol):
    def create(self, curriculum: CurriculumDTO) -> CurriculumDTO: ...

    def save(self, curriculum: CurriculumDTO) -> CurriculumDTO: ...

    def get_by_id(self, curriculum_id: CurriculumId) -> CurriculumDTO: ...

    def list_by_goal_id(self, goal_id: GoalId) -> list[CurriculumDTO]: ...

    def list_by_run_id(self, run_id: RunId) -> list[CurriculumDTO]: ...

    def list_by_knowledge_map_id(
        self,
        knowledge_map_id: KnowledgeMapId,
    ) -> list[CurriculumDTO]: ...

    def update_status(
        self,
        curriculum_id: CurriculumId,
        status: CurriculumStatus,
    ) -> CurriculumDTO: ...

    def clear(self) -> None: ...
