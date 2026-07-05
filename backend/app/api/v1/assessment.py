from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import AssessmentServiceDependency
from app.schemas.assessment import AssessmentSessionDTO
from app.schemas.ids import AssessmentId

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/{assessment_id}", response_model=AssessmentSessionDTO)
def get_assessment(
    assessment_id: AssessmentId,
    service: AssessmentServiceDependency,
) -> AssessmentSessionDTO:
    return service.get_session_by_id(assessment_id)
