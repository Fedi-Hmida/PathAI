from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.dependencies import (
    ApiContainerDependency,
    AuthorizationDependency,
    CurrentUserOrNoneDependency,
    OrchestrationRunServiceDependency,
)
from app.core.settings import Settings, get_settings
from app.schemas.enums import OrchestrationRunStatus
from app.schemas.ids import RunId
from app.schemas.orchestration import OrchestrationRunDTO, OrchestrationStatusResponse
from app.services.dashboard import RUN_STATUS_MAP

router = APIRouter(prefix="/orchestration/runs", tags=["orchestration"])
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.post("", response_model=OrchestrationRunDTO)
def trigger_orchestration_run(
    container: ApiContainerDependency,
    settings: SettingsDependency,
) -> OrchestrationRunDTO:
    if not settings.enable_orchestration_run_route:
        raise HTTPException(status_code=404, detail="orchestration run route is disabled")
    return container.run_demo_pipeline()


@router.get("/{run_id}", response_model=OrchestrationRunDTO)
def get_orchestration_run(
    run_id: RunId,
    service: OrchestrationRunServiceDependency,
    current_user: CurrentUserOrNoneDependency,
    authz: AuthorizationDependency,
) -> OrchestrationRunDTO:
    authz.assert_run_access(current_user, run_id)
    return service.get_by_id(run_id)


@router.get("/{run_id}/status", response_model=OrchestrationStatusResponse)
def get_orchestration_status(
    run_id: RunId,
    service: OrchestrationRunServiceDependency,
    current_user: CurrentUserOrNoneDependency,
    authz: AuthorizationDependency,
) -> OrchestrationStatusResponse:
    authz.assert_run_access(current_user, run_id)
    run = service.get_by_id(run_id)
    return OrchestrationStatusResponse(
        run_id=run.run_id,
        status=RUN_STATUS_MAP[run.status],
        current_node=run.current_node,
        requires_user_input=run.status == OrchestrationRunStatus.REQUIRES_INPUT,
    )
