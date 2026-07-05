from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import EvaluationServiceDependency
from app.schemas.evaluation import EvaluationReportDTO
from app.schemas.ids import EvaluationReportId

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/{evaluation_id}", response_model=EvaluationReportDTO)
def get_evaluation(
    evaluation_id: EvaluationReportId,
    service: EvaluationServiceDependency,
) -> EvaluationReportDTO:
    return service.get_by_id(evaluation_id)
