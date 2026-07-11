from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.dependencies import ApiContainerDependency, require_auth_disabled
from app.api.v1.responses import DemoLoadFixturesResponse

# The demo loader clears ALL data, so it is disabled (404) when auth is on to
# avoid wiping per-user workspaces; per-user seeding replaces it in that mode.
router = APIRouter(
    prefix="/demo",
    tags=["demo"],
    dependencies=[Depends(require_auth_disabled)],
)


@router.post("/load-fixtures", response_model=DemoLoadFixturesResponse)
def load_demo_fixtures(container: ApiContainerDependency) -> DemoLoadFixturesResponse:
    return container.load_canonical_demo()
