from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import (
    AuthorizationDependency,
    CurrentUserOrNoneDependency,
    EvaluationServiceDependency,
)
from app.schemas.evaluation import EvaluationReportDTO
from app.schemas.ids import EvaluationReportId

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.get("/{evaluation_id}", response_model=EvaluationReportDTO)
def get_evaluation(
    evaluation_id: EvaluationReportId,
    service: EvaluationServiceDependency,
    current_user: CurrentUserOrNoneDependency,
    authz: AuthorizationDependency,
) -> EvaluationReportDTO:
    evaluation = service.get_by_id(evaluation_id)
    authz.assert_goal_access(current_user, evaluation.goal_id)
    return evaluation
