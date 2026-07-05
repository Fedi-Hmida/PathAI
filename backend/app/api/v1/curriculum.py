from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import CurriculumServiceDependency
from app.schemas.curriculum import CurriculumDTO
from app.schemas.ids import CurriculumId

router = APIRouter(prefix="/curricula", tags=["curricula"])


@router.get("/{curriculum_id}", response_model=CurriculumDTO)
def get_curriculum(
    curriculum_id: CurriculumId,
    service: CurriculumServiceDependency,
) -> CurriculumDTO:
    return service.get_by_id(curriculum_id)
