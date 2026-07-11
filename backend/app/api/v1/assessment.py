from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import (
    AssessmentServiceDependency,
    AuthorizationDependency,
    CurrentUserOrNoneDependency,
)
from app.schemas.assessment import AssessmentAnswerDTO, AssessmentSessionDTO
from app.schemas.ids import AssessmentId

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("/{assessment_id}", response_model=AssessmentSessionDTO)
def get_assessment(
    assessment_id: AssessmentId,
    service: AssessmentServiceDependency,
    current_user: CurrentUserOrNoneDependency,
    authz: AuthorizationDependency,
) -> AssessmentSessionDTO:
    session = service.get_session_by_id(assessment_id)
    authz.assert_goal_access(current_user, session.goal_id)
    return session


@router.get("/{assessment_id}/answers", response_model=list[AssessmentAnswerDTO])
def list_assessment_answers(
    assessment_id: AssessmentId,
    service: AssessmentServiceDependency,
    current_user: CurrentUserOrNoneDependency,
    authz: AuthorizationDependency,
) -> list[AssessmentAnswerDTO]:
    # Authorize via the parent session's goal so the answer list can't be
    # read for someone else's assessment.
    session = service.get_session_by_id(assessment_id)
    authz.assert_goal_access(current_user, session.goal_id)
    return service.list_answers_by_session_id(assessment_id)
