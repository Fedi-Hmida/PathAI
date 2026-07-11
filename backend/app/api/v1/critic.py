from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import (
    AuthorizationDependency,
    CriticServiceDependency,
    CurrentUserOrNoneDependency,
)
from app.schemas.critic import CriticReviewDTO
from app.schemas.ids import CriticReviewId

router = APIRouter(prefix="/critic-reviews", tags=["critic-reviews"])


@router.get("/{critic_id}", response_model=CriticReviewDTO)
def get_critic_review(
    critic_id: CriticReviewId,
    service: CriticServiceDependency,
    current_user: CurrentUserOrNoneDependency,
    authz: AuthorizationDependency,
) -> CriticReviewDTO:
    critic_review = service.get_by_id(critic_id)
    authz.assert_goal_access(current_user, critic_review.goal_id)
    return critic_review
