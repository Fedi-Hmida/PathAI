from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import (
    AuthorizationDependency,
    CurrentUserOrNoneDependency,
    CurriculumServiceDependency,
)
from app.schemas.curriculum import CurriculumDTO
from app.schemas.ids import CurriculumId

router = APIRouter(prefix="/curricula", tags=["curricula"])


@router.get("/{curriculum_id}", response_model=CurriculumDTO)
def get_curriculum(
    curriculum_id: CurriculumId,
    service: CurriculumServiceDependency,
    current_user: CurrentUserOrNoneDependency,
    authz: AuthorizationDependency,
) -> CurriculumDTO:
    curriculum = service.get_by_id(curriculum_id)
    authz.assert_goal_access(current_user, curriculum.goal_id)
    return curriculum
