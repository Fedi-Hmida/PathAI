from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import DashboardServiceDependency
from app.schemas.dashboard import DashboardPayload
from app.schemas.ids import RunId

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{run_id}", response_model=DashboardPayload)
def get_dashboard(run_id: RunId, service: DashboardServiceDependency) -> DashboardPayload:
    return service.get_by_run_id(run_id)
