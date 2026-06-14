from fastapi import APIRouter

from app.api.v1.runtime_services import build_runtime_services
from app.core.errors import PathAIError
from app.progress.errors import ProgressError
from app.progress.schemas import (
    CurriculumProgressSummary,
    ProgressInitializeRequest,
    ProgressInitializeResponse,
    ProgressUpdateRequest,
    ProgressUpdateResponse,
    WeekProgressResponse,
)
from app.progress.service import ProgressService

router = APIRouter(prefix="/progress", tags=["progress"])
progress_service: ProgressService = build_runtime_services().progress


@router.post(
    "/initialize",
    response_model=ProgressInitializeResponse,
    summary="Initialize temporary no-auth progress tracking from a curriculum.",
)
async def initialize_progress(
    request: ProgressInitializeRequest,
) -> ProgressInitializeResponse:
    try:
        return progress_service.initialize_progress(request)
    except ProgressError as exc:
        raise _to_pathai_error(exc) from exc


@router.post(
    "/update",
    response_model=ProgressUpdateResponse,
    summary="Update topic progress status in the temporary progress store.",
)
async def update_progress(request: ProgressUpdateRequest) -> ProgressUpdateResponse:
    try:
        return progress_service.update_progress(request)
    except ProgressError as exc:
        raise _to_pathai_error(exc) from exc


@router.get(
    "/{curriculum_id}",
    response_model=CurriculumProgressSummary,
    summary="Return a temporary no-auth curriculum progress summary.",
)
async def get_progress_summary(curriculum_id: str) -> CurriculumProgressSummary:
    try:
        return progress_service.get_summary(curriculum_id)
    except ProgressError as exc:
        raise _to_pathai_error(exc) from exc


@router.get(
    "/{curriculum_id}/week/{week_number}",
    response_model=WeekProgressResponse,
    summary="Return a temporary no-auth week progress summary.",
)
async def get_week_progress(curriculum_id: str, week_number: int) -> WeekProgressResponse:
    try:
        return progress_service.get_week(curriculum_id, week_number)
    except ProgressError as exc:
        raise _to_pathai_error(exc) from exc


def _to_pathai_error(exc: ProgressError) -> PathAIError:
    return PathAIError(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
