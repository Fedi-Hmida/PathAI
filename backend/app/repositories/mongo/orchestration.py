from __future__ import annotations

from typing import Any

from pymongo.collection import Collection

from app.repositories.mongo.base import MongoStore
from app.schemas.enums import OrchestrationRunStatus
from app.schemas.ids import GoalId, RunId
from app.schemas.orchestration import OrchestrationRunDTO, WorkflowNodeEvent


class MongoOrchestrationRunRepository:
    def __init__(self, collection: Collection[dict[str, Any]]) -> None:
        self._runs: MongoStore[OrchestrationRunDTO] = MongoStore(
            collection,
            OrchestrationRunDTO,
            "orchestration run",
        )

    def create(self, run: OrchestrationRunDTO) -> OrchestrationRunDTO:
        return self._runs.create(run.run_id, run)

    def save(self, run: OrchestrationRunDTO) -> OrchestrationRunDTO:
        return self._runs.save(run.run_id, run)

    def get_by_id(self, run_id: RunId) -> OrchestrationRunDTO:
        return self._runs.get(run_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[OrchestrationRunDTO]:
        return self._runs.list_where("goal_id", goal_id)

    def update_status(
        self,
        run_id: RunId,
        status: OrchestrationRunStatus,
    ) -> OrchestrationRunDTO:
        return self._runs.update_fields(run_id, status=status)

    def append_event(self, run_id: RunId, event: WorkflowNodeEvent) -> OrchestrationRunDTO:
        run = self._runs.get(run_id)
        node_events = [*run.node_events, event]
        return self._runs.update_fields(run_id, node_events=node_events)

    def delete(self, run_id: RunId) -> None:
        self._runs.delete(run_id)

    def clear(self) -> None:
        self._runs.clear()
