from fastapi import APIRouter

from app.api.v1.assessment import assessment_service
from app.assessment.errors import AssessmentError
from app.assessment.schemas import AssessmentSessionState
from app.core.errors import PathAIError
from app.curriculum.errors import CurriculumError, CurriculumInputError
from app.curriculum.schemas import (
    CurriculumGenerateResponse,
    CurriculumGenerationRequest,
    CurriculumResponse,
    CurriculumValidationResponse,
)
from app.curriculum.service import CurriculumService

router = APIRouter(prefix="/curriculum", tags=["curriculum"])
curriculum_service = CurriculumService()


@router.post(
    "/generate",
    response_model=CurriculumGenerateResponse,
    summary="Generate a temporary no-auth curriculum from assessment evidence.",
)
async def generate_curriculum(
    request: CurriculumGenerationRequest,
) -> CurriculumGenerateResponse:
    try:
        resolved = _resolve_assessment_request(request)
        return await curriculum_service.generate_curriculum(resolved)
    except (AssessmentError, CurriculumError) as exc:
        raise _to_pathai_error(exc) from exc


@router.get(
    "/{curriculum_id}",
    response_model=CurriculumResponse,
    summary="Get a temporary no-auth generated curriculum.",
)
async def get_curriculum(curriculum_id: str) -> CurriculumResponse:
    try:
        return curriculum_service.get_curriculum(curriculum_id)
    except CurriculumError as exc:
        raise _to_pathai_error(exc) from exc


@router.post(
    "/validate",
    response_model=CurriculumValidationResponse,
    summary="Validate that a curriculum request can produce a structurally valid draft.",
)
async def validate_curriculum_request(
    request: CurriculumGenerationRequest,
) -> CurriculumValidationResponse:
    try:
        resolved = _resolve_assessment_request(request)
        return curriculum_service.validate_request(resolved)
    except (AssessmentError, CurriculumError) as exc:
        raise _to_pathai_error(exc) from exc


def _resolve_assessment_request(
    request: CurriculumGenerationRequest,
) -> CurriculumGenerationRequest:
    if not request.assessment_session_id:
        return request

    session = assessment_service.get_session(request.assessment_session_id)
    _ensure_completed_assessment(session)

    return request.model_copy(
        update={
            "user_id": request.user_id or session.user_id,
            "goal_id": request.goal_id or session.goal_id,
            "goal": request.goal or session.goal,
            "timeline_weeks": request.timeline_weeks or session.timeline_weeks,
            "hours_per_week": request.hours_per_week or session.hours_per_week,
            "knowledge_map": request.knowledge_map or session.knowledge_map,
        }
    )


def _ensure_completed_assessment(session: AssessmentSessionState) -> None:
    if session.status != "completed" or session.knowledge_map is None:
        raise CurriculumInputError(
            code="assessment_not_ready_for_curriculum",
            message="Assessment must be completed before curriculum generation.",
            status_code=409,
        )


def _to_pathai_error(exc: AssessmentError | CurriculumError) -> PathAIError:
    return PathAIError(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
    )
