from __future__ import annotations

from dataclasses import dataclass

from app.repositories.protocols.curriculum import CurriculumRepository
from app.schemas.curriculum import CurriculumDTO
from app.schemas.enums import CurriculumStatus
from app.schemas.ids import CurriculumId, GoalId, KnowledgeMapId, RunId


@dataclass(slots=True)
class CurriculumService:
    repository: CurriculumRepository

    def create(self, curriculum: CurriculumDTO) -> CurriculumDTO:
        return self.repository.create(curriculum)

    def save(self, curriculum: CurriculumDTO) -> CurriculumDTO:
        return self.repository.save(curriculum)

    def get_by_id(self, curriculum_id: CurriculumId) -> CurriculumDTO:
        return self.repository.get_by_id(curriculum_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[CurriculumDTO]:
        return self.repository.list_by_goal_id(goal_id)

    def list_by_run_id(self, run_id: RunId) -> list[CurriculumDTO]:
        return self.repository.list_by_run_id(run_id)

    def list_by_knowledge_map_id(self, knowledge_map_id: KnowledgeMapId) -> list[CurriculumDTO]:
        return self.repository.list_by_knowledge_map_id(knowledge_map_id)

    def update_status(
        self,
        curriculum_id: CurriculumId,
        status: CurriculumStatus,
    ) -> CurriculumDTO:
        return self.repository.update_status(curriculum_id, status)
