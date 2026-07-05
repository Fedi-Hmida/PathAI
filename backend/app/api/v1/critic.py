from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import CriticServiceDependency
from app.schemas.critic import CriticReviewDTO
from app.schemas.ids import CriticReviewId

router = APIRouter(prefix="/critic-reviews", tags=["critic-reviews"])


@router.get("/{critic_id}", response_model=CriticReviewDTO)
def get_critic_review(
    critic_id: CriticReviewId,
    service: CriticServiceDependency,
) -> CriticReviewDTO:
    return service.get_by_id(critic_id)
