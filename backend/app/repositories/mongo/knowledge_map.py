from __future__ import annotations

from typing import Any

from pymongo.collection import Collection

from app.repositories.mongo.base import MongoStore
from app.schemas.enums import KnowledgeMapStatus
from app.schemas.ids import GoalId, KnowledgeMapId, RunId
from app.schemas.knowledge_map import KnowledgeMapDTO


class MongoKnowledgeMapRepository:
    def __init__(self, collection: Collection[dict[str, Any]]) -> None:
        self._knowledge_maps: MongoStore[KnowledgeMapDTO] = MongoStore(
            collection,
            KnowledgeMapDTO,
            "knowledge map",
        )

    def create(self, knowledge_map: KnowledgeMapDTO) -> KnowledgeMapDTO:
        return self._knowledge_maps.create(knowledge_map.knowledge_map_id, knowledge_map)

    def save(self, knowledge_map: KnowledgeMapDTO) -> KnowledgeMapDTO:
        return self._knowledge_maps.save(knowledge_map.knowledge_map_id, knowledge_map)

    def get_by_id(self, knowledge_map_id: KnowledgeMapId) -> KnowledgeMapDTO:
        return self._knowledge_maps.get(knowledge_map_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[KnowledgeMapDTO]:
        return self._knowledge_maps.list_where("goal_id", goal_id)

    def list_by_run_id(self, run_id: RunId) -> list[KnowledgeMapDTO]:
        return self._knowledge_maps.list_where("run_id", run_id)

    def update_status(
        self,
        knowledge_map_id: KnowledgeMapId,
        status: KnowledgeMapStatus,
    ) -> KnowledgeMapDTO:
        return self._knowledge_maps.update_fields(knowledge_map_id, status=status)

    def clear(self) -> None:
        self._knowledge_maps.clear()
