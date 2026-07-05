from __future__ import annotations

from dataclasses import dataclass

from app.repositories.protocols.knowledge_map import KnowledgeMapRepository
from app.schemas.enums import KnowledgeMapStatus
from app.schemas.ids import GoalId, KnowledgeMapId, RunId
from app.schemas.knowledge_map import KnowledgeMapDTO


@dataclass(slots=True)
class KnowledgeMapService:
    repository: KnowledgeMapRepository

    def create(self, knowledge_map: KnowledgeMapDTO) -> KnowledgeMapDTO:
        return self.repository.create(knowledge_map)

    def save(self, knowledge_map: KnowledgeMapDTO) -> KnowledgeMapDTO:
        return self.repository.save(knowledge_map)

    def get_by_id(self, knowledge_map_id: KnowledgeMapId) -> KnowledgeMapDTO:
        return self.repository.get_by_id(knowledge_map_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[KnowledgeMapDTO]:
        return self.repository.list_by_goal_id(goal_id)

    def list_by_run_id(self, run_id: RunId) -> list[KnowledgeMapDTO]:
        return self.repository.list_by_run_id(run_id)

    def update_status(
        self,
        knowledge_map_id: KnowledgeMapId,
        status: KnowledgeMapStatus,
    ) -> KnowledgeMapDTO:
        return self.repository.update_status(knowledge_map_id, status)
