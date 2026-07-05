from __future__ import annotations

from dataclasses import dataclass

from app.repositories.protocols.orchestration import OrchestrationRunRepository
from app.schemas.enums import OrchestrationRunStatus
from app.schemas.ids import GoalId, RunId
from app.schemas.orchestration import OrchestrationRunDTO, WorkflowNodeEvent


@dataclass(slots=True)
class OrchestrationRunService:
    repository: OrchestrationRunRepository

    def create(self, run: OrchestrationRunDTO) -> OrchestrationRunDTO:
        return self.repository.create(run)

    def save(self, run: OrchestrationRunDTO) -> OrchestrationRunDTO:
        return self.repository.save(run)

    def get_by_id(self, run_id: RunId) -> OrchestrationRunDTO:
        return self.repository.get_by_id(run_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[OrchestrationRunDTO]:
        return self.repository.list_by_goal_id(goal_id)

    def update_status(self, run_id: RunId, status: OrchestrationRunStatus) -> OrchestrationRunDTO:
        return self.repository.update_status(run_id, status)

    def append_event(self, run_id: RunId, event: WorkflowNodeEvent) -> OrchestrationRunDTO:
        return self.repository.append_event(run_id, event)
