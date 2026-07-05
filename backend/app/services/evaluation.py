from __future__ import annotations

from dataclasses import dataclass

from app.repositories.protocols.evaluation import EvaluationRepository
from app.schemas.evaluation import EvaluationReportDTO
from app.schemas.ids import EvaluationReportId, GoalId, RunId


@dataclass(slots=True)
class EvaluationService:
    repository: EvaluationRepository

    def create(self, evaluation_report: EvaluationReportDTO) -> EvaluationReportDTO:
        return self.repository.create(evaluation_report)

    def save(self, evaluation_report: EvaluationReportDTO) -> EvaluationReportDTO:
        return self.repository.save(evaluation_report)

    def get_by_id(self, evaluation_report_id: EvaluationReportId) -> EvaluationReportDTO:
        return self.repository.get_by_id(evaluation_report_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[EvaluationReportDTO]:
        return self.repository.list_by_goal_id(goal_id)

    def list_by_run_id(self, run_id: RunId) -> list[EvaluationReportDTO]:
        return self.repository.list_by_run_id(run_id)
