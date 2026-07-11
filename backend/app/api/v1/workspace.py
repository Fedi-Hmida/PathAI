from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.dependencies import (
    CurrentUserDependency,
    WorkspaceServiceDependency,
    require_auth_enabled,
)
from app.schemas.workspace import WorkspaceRef

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
    user: CurrentUserDependency,
    service: WorkspaceServiceDependency,
) -> WorkspaceRef:
    # WorkspaceExistsError -> 409 via the registered exception handler.
    return WorkspaceRef(run_id=service.seed(user))


@router.post("/reset", response_model=WorkspaceRef)
def reset_my_workspace(
    user: CurrentUserDependency,
    service: WorkspaceServiceDependency,
) -> WorkspaceRef:
    return WorkspaceRef(run_id=service.reset(user))
