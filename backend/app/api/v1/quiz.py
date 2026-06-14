from fastapi import APIRouter

from app.api.v1.runtime_services import build_runtime_services
from app.core.errors import PathAIError
from app.quiz.errors import QuizError
from app.quiz.schemas import (
    Quiz,
    QuizGenerateResponse,
    QuizGenerationRequest,
    QuizHistorySummary,
    QuizResult,
    QuizSubmissionRequest,
)
from app.quiz.service import QuizService

router = APIRouter(prefix="/quiz", tags=["quiz"])
quiz_service: QuizService = build_runtime_services().quiz


@router.post(
    "/generate",
    response_model=QuizGenerateResponse,
    summary="Generate a temporary no-auth weekly quiz from a curriculum week.",
)
async def generate_quiz(request: QuizGenerationRequest) -> QuizGenerateResponse:
    try:
        return await quiz_service.generate_quiz(request)
    except QuizError as exc:
        raise _to_pathai_error(exc) from exc


@router.get(
    "/{quiz_id}",
    response_model=Quiz,
    summary="Return a temporary no-auth quiz by ID.",
)
async def get_quiz(quiz_id: str) -> Quiz:
    try:
        return quiz_service.get_quiz(quiz_id)
    except QuizError as exc:
        raise _to_pathai_error(exc) from exc


@router.post(
    "/{quiz_id}/submit",
    response_model=QuizResult,
    summary="Submit quiz answers and return deterministic score/feedback.",
)
async def submit_quiz(
    quiz_id: str,
    request: QuizSubmissionRequest,
) -> QuizResult:
    try:
        return quiz_service.submit_quiz(quiz_id, request)
    except QuizError as exc:
        raise _to_pathai_error(exc) from exc


@router.get(
    "/{curriculum_id}/history",
    response_model=QuizHistorySummary,
    summary="Return temporary no-auth quiz attempt history for a curriculum.",
)
async def get_quiz_history(curriculum_id: str) -> QuizHistorySummary:
    return quiz_service.get_history(curriculum_id)


def _to_pathai_error(exc: QuizError) -> PathAIError:
    return PathAIError(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
