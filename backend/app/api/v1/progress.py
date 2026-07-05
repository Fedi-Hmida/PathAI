from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import ProgressServiceDependency
from app.schemas.ids import ProgressId
from app.schemas.progress import ProgressStateDTO

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/{progress_id}", response_model=ProgressStateDTO)
def get_progress(
    progress_id: ProgressId,
    service: ProgressServiceDependency,
) -> ProgressStateDTO:
    return service.get_by_id(progress_id)
