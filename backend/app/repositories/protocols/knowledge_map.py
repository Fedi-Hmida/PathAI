from __future__ import annotations

from typing import Protocol

from app.schemas.enums import KnowledgeMapStatus
from app.schemas.ids import GoalId, KnowledgeMapId, RunId
from app.schemas.knowledge_map import KnowledgeMapDTO


class KnowledgeMapRepository(Protocol):
    def create(self, knowledge_map: KnowledgeMapDTO) -> KnowledgeMapDTO: ...

    def save(self, knowledge_map: KnowledgeMapDTO) -> KnowledgeMapDTO: ...

    def get_by_id(self, knowledge_map_id: KnowledgeMapId) -> KnowledgeMapDTO: ...

    def list_by_goal_id(self, goal_id: GoalId) -> list[KnowledgeMapDTO]: ...

    def list_by_run_id(self, run_id: RunId) -> list[KnowledgeMapDTO]: ...

    def update_status(
        self,
        knowledge_map_id: KnowledgeMapId,
        status: KnowledgeMapStatus,
    ) -> KnowledgeMapDTO: ...

    def clear(self) -> None: ...
