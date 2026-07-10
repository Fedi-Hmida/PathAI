from __future__ import annotations

from typing import Any

from pymongo.collection import Collection

from app.repositories.mongo.base import MongoStore
from app.schemas.curriculum import CurriculumDTO
from app.schemas.enums import CurriculumStatus
from app.schemas.ids import CurriculumId, GoalId, KnowledgeMapId, RunId


class MongoCurriculumRepository:
    def __init__(self, collection: Collection[dict[str, Any]]) -> None:
        self._curricula: MongoStore[CurriculumDTO] = MongoStore(
            collection,
            CurriculumDTO,
            "curriculum",
        )

    def create(self, curriculum: CurriculumDTO) -> CurriculumDTO:
        return self._curricula.create(curriculum.curriculum_id, curriculum)

    def save(self, curriculum: CurriculumDTO) -> CurriculumDTO:
        return self._curricula.save(curriculum.curriculum_id, curriculum)

    def get_by_id(self, curriculum_id: CurriculumId) -> CurriculumDTO:
        return self._curricula.get(curriculum_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[CurriculumDTO]:
        return self._curricula.list_where("goal_id", goal_id)

    def list_by_run_id(self, run_id: RunId) -> list[CurriculumDTO]:
        return self._curricula.list_where("run_id", run_id)

    def list_by_knowledge_map_id(self, knowledge_map_id: KnowledgeMapId) -> list[CurriculumDTO]:
        return self._curricula.list_where("knowledge_map_id", knowledge_map_id)

    def update_status(
        self,
        curriculum_id: CurriculumId,
        status: CurriculumStatus,
    ) -> CurriculumDTO:
        return self._curricula.update_fields(curriculum_id, status=status)

    def clear(self) -> None:
        self._curricula.clear()
