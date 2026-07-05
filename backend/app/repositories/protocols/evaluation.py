from __future__ import annotations

from typing import Protocol

from app.schemas.evaluation import EvaluationReportDTO
from app.schemas.ids import EvaluationReportId, GoalId, RunId


class EvaluationRepository(Protocol):
    def create(self, evaluation_report: EvaluationReportDTO) -> EvaluationReportDTO: ...

    def save(self, evaluation_report: EvaluationReportDTO) -> EvaluationReportDTO: ...

    def get_by_id(self, evaluation_report_id: EvaluationReportId) -> EvaluationReportDTO: ...

    def list_by_goal_id(self, goal_id: GoalId) -> list[EvaluationReportDTO]: ...

    def list_by_run_id(self, run_id: RunId) -> list[EvaluationReportDTO]: ...

    def clear(self) -> None: ...
