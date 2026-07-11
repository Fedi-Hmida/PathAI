from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import (
    AuthorizationDependency,
    CurrentUserOrNoneDependency,
    ProgressServiceDependency,
)
from app.schemas.ids import ProgressId
from app.schemas.progress import ProgressStateDTO

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/{progress_id}", response_model=ProgressStateDTO)
def get_progress(
    progress_id: ProgressId,
    service: ProgressServiceDependency,
    current_user: CurrentUserOrNoneDependency,
    authz: AuthorizationDependency,
) -> ProgressStateDTO:
    progress = service.get_by_id(progress_id)
    authz.assert_goal_access(current_user, progress.goal_id)
    return progress
