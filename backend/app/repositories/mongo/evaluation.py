from __future__ import annotations

from typing import Any

from pymongo.collection import Collection

from app.repositories.mongo.base import MongoStore
from app.schemas.evaluation import EvaluationReportDTO
from app.schemas.ids import EvaluationReportId, GoalId, RunId


class MongoEvaluationRepository:
    def __init__(self, collection: Collection[dict[str, Any]]) -> None:
        self._evaluation_reports: MongoStore[EvaluationReportDTO] = MongoStore(
            collection,
            EvaluationReportDTO,
            "evaluation report",
        )

    def create(self, evaluation_report: EvaluationReportDTO) -> EvaluationReportDTO:
        return self._evaluation_reports.create(
            evaluation_report.evaluation_report_id,
            evaluation_report,
        )

    def save(self, evaluation_report: EvaluationReportDTO) -> EvaluationReportDTO:
        return self._evaluation_reports.save(
            evaluation_report.evaluation_report_id,
            evaluation_report,
        )

    def get_by_id(self, evaluation_report_id: EvaluationReportId) -> EvaluationReportDTO:
        return self._evaluation_reports.get(evaluation_report_id)

    def list_by_goal_id(self, goal_id: GoalId) -> list[EvaluationReportDTO]:
        return self._evaluation_reports.list_where("goal_id", goal_id)

    def list_by_run_id(self, run_id: RunId) -> list[EvaluationReportDTO]:
        return self._evaluation_reports.list_where("run_id", run_id)

    def clear(self) -> None:
        self._evaluation_reports.clear()
