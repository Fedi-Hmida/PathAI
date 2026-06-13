from fastapi import APIRouter

from app.assessment.errors import AssessmentError
from app.assessment.schemas import (
    AnswerSubmissionRequest,
    AssessmentSessionResponse,
    FinalizeAssessmentResponse,
    GoalIntakeRequest,
    StartAssessmentResponse,
    SubmitAnswerResponse,
)
from app.assessment.service import AssessmentService
from app.core.errors import PathAIError

router = APIRouter(prefix="/assessment", tags=["assessment"])
assessment_service = AssessmentService()


@router.post(
    "/start",
    response_model=StartAssessmentResponse,
    summary="Start a temporary no-auth assessment session.",
)
async def start_assessment(request: GoalIntakeRequest) -> StartAssessmentResponse:
    return await assessment_service.start_assessment(request)


@router.get(
    "/{session_id}",
    response_model=AssessmentSessionResponse,
    summary="Get temporary no-auth assessment session state.",
)
async def get_assessment_session(session_id: str) -> AssessmentSessionResponse:
    try:
        return AssessmentSessionResponse(session=assessment_service.get_session(session_id))
    except AssessmentError as exc:
        raise _to_pathai_error(exc) from exc


@router.post(
    "/{session_id}/answer",
    response_model=SubmitAnswerResponse,
    summary="Submit an assessment answer and get the next question or result.",
)
async def submit_assessment_answer(
    session_id: str,
    request: AnswerSubmissionRequest,
) -> SubmitAnswerResponse:
    try:
        return await assessment_service.submit_answer(session_id, request)
    except AssessmentError as exc:
        raise _to_pathai_error(exc) from exc


@router.post(
    "/{session_id}/finalize",
    response_model=FinalizeAssessmentResponse,
    summary="Force final knowledge map generation for a temporary assessment session.",
)
async def finalize_assessment(session_id: str) -> FinalizeAssessmentResponse:
    try:
        return assessment_service.finalize_assessment(session_id)
    except AssessmentError as exc:
        raise _to_pathai_error(exc) from exc


def _to_pathai_error(exc: AssessmentError) -> PathAIError:
    return PathAIError(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
    )
