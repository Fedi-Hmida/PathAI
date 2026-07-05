from __future__ import annotations

from typing import Protocol

from app.schemas.enums import OrchestrationRunStatus
from app.schemas.ids import GoalId, RunId
from app.schemas.orchestration import OrchestrationRunDTO, WorkflowNodeEvent


class OrchestrationRunRepository(Protocol):
    def create(self, run: OrchestrationRunDTO) -> OrchestrationRunDTO: ...

    def save(self, run: OrchestrationRunDTO) -> OrchestrationRunDTO: ...

    def get_by_id(self, run_id: RunId) -> OrchestrationRunDTO: ...

    def list_by_goal_id(self, goal_id: GoalId) -> list[OrchestrationRunDTO]: ...

    def update_status(
        self,
        run_id: RunId,
        status: OrchestrationRunStatus,
    ) -> OrchestrationRunDTO: ...

    def append_event(self, run_id: RunId, event: WorkflowNodeEvent) -> OrchestrationRunDTO: ...

    def clear(self) -> None: ...
