from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import (
    CurrentUserDependency,
    WorkspaceGenerationServiceDependency,
    WorkspaceServiceDependency,
    require_auth_enabled,
)
from app.schemas.goal import LearningGoalCreate
from app.schemas.workspace import WorkspaceGenerationResult, WorkspaceRef

# The whole router requires auth; it is invisible (404) when auth is disabled.
router = APIRouter(
    prefix="/me/workspace",
    tags=["workspace"],
    dependencies=[Depends(require_auth_enabled)],
)


@router.get("", response_model=WorkspaceRef)
def get_my_workspace(
    user: CurrentUserDependency,
    service: WorkspaceServiceDependency,
) -> WorkspaceRef:
    run_id = service.get_run_id(user)
    if run_id is None:
        raise HTTPException(status_code=404, detail="no workspace")
    return WorkspaceRef(run_id=run_id)


@router.post("", response_model=WorkspaceRef, status_code=status.HTTP_201_CREATED)
def create_my_workspace(
    payload: LearningGoalCreate,
    user: CurrentUserDependency,
    service: WorkspaceServiceDependency,
) -> WorkspaceRef:
    # WorkspaceExistsError -> 409 via the registered exception handler.
    return WorkspaceRef(
        run_id=service.seed(user, payload.goal_text, payload.learner_profile),
    )


@router.post("/reset", response_model=WorkspaceRef)
def reset_my_workspace(
    payload: LearningGoalCreate,
    user: CurrentUserDependency,
    service: WorkspaceServiceDependency,
) -> WorkspaceRef:
    return WorkspaceRef(
        run_id=service.reset(user, payload.goal_text, payload.learner_profile),
    )


@router.post("/generate", response_model=WorkspaceGenerationResult)
def generate_my_workspace(
    user: CurrentUserDependency,
    workspace: WorkspaceServiceDependency,
    generation: WorkspaceGenerationServiceDependency,
) -> WorkspaceGenerationResult:
    """Build (or regenerate) the caller's knowledge map + curriculum from
    their own completed live assessment. A fresh workspace seeds neither, so
    the first call creates them; later calls regenerate in place.
    AssessmentNotCompleteError -> 409 via the registered exception handler."""
    goal = workspace.get_owned_goal(user)
    if goal is None:
        raise HTTPException(status_code=404, detail="no workspace")
    knowledge_map, curriculum = generation.generate(goal)
    return WorkspaceGenerationResult(
        knowledge_map_id=knowledge_map.knowledge_map_id,
        curriculum_id=curriculum.curriculum_id,
    )
