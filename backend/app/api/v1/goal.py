from __future__ import annotations

from fastapi import APIRouter, status

from app.api.v1.dependencies import (
    AuthorizationDependency,
    CurrentUserOrNoneDependency,
    GoalServiceDependency,
    build_learning_goal,
)
from app.schemas.goal import LearningGoalCreate, LearningGoalDTO
from app.schemas.ids import GoalId

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=LearningGoalDTO, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: LearningGoalCreate,
    service: GoalServiceDependency,
) -> LearningGoalDTO:
    return service.create(build_learning_goal(payload))


@router.get("/{goal_id}", response_model=LearningGoalDTO)
def get_goal(
    goal_id: GoalId,
    service: GoalServiceDependency,
    current_user: CurrentUserOrNoneDependency,
    authz: AuthorizationDependency,
) -> LearningGoalDTO:
    authz.assert_goal_access(current_user, goal_id)
    return service.get_by_id(goal_id)
