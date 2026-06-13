from fastapi import APIRouter

from app.core.errors import PathAIError
from app.critic.errors import CriticError
from app.critic.schemas import (
    CriticCurriculumOnlyRequest,
    CriticReviewRequest,
    CriticReviewResult,
    CriticRubricSummary,
)
from app.critic.service import CriticService

router = APIRouter(prefix="/critic", tags=["critic"])
critic_service = CriticService()


@router.post(
    "/review",
    response_model=CriticReviewResult,
    summary="Review curriculum and optional resource attachments with the Critic rubric.",
)
async def review_curriculum_with_resources(
    request: CriticReviewRequest,
) -> CriticReviewResult:
    try:
        return await critic_service.review_curriculum_with_resources(request)
    except CriticError as exc:
        raise _to_pathai_error(exc) from exc


@router.post(
    "/review-curriculum",
    response_model=CriticReviewResult,
    summary="Review curriculum structure without requiring resource attachments.",
)
async def review_curriculum_only(
    request: CriticCurriculumOnlyRequest,
) -> CriticReviewResult:
    try:
        return await critic_service.review_curriculum(request)
    except CriticError as exc:
        raise _to_pathai_error(exc) from exc


@router.get(
    "/rubric",
    response_model=CriticRubricSummary,
    summary="Return deterministic Critic rubric criteria and thresholds.",
)
async def get_critic_rubric() -> CriticRubricSummary:
    return critic_service.get_critic_rubric_summary()


def _to_pathai_error(exc: CriticError) -> PathAIError:
    return PathAIError(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
