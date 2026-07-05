from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import OrchestrationRunServiceDependency
from app.schemas.enums import OrchestrationRunStatus
from app.schemas.ids import RunId
from app.schemas.orchestration import OrchestrationRunDTO, OrchestrationStatusResponse
from app.services.dashboard import RUN_STATUS_MAP

router = APIRouter(prefix="/orchestration/runs", tags=["orchestration"])


@router.get("/{run_id}", response_model=OrchestrationRunDTO)
def get_orchestration_run(
    run_id: RunId,
    service: OrchestrationRunServiceDependency,
) -> OrchestrationRunDTO:
    return service.get_by_id(run_id)


@router.get("/{run_id}/status", response_model=OrchestrationStatusResponse)
def get_orchestration_status(
    run_id: RunId,
    service: OrchestrationRunServiceDependency,
) -> OrchestrationStatusResponse:
    run = service.get_by_id(run_id)
    return OrchestrationStatusResponse(
        run_id=run.run_id,
        status=RUN_STATUS_MAP[run.status],
        current_node=run.current_node,
        requires_user_input=run.status == OrchestrationRunStatus.REQUIRES_INPUT,
    )
