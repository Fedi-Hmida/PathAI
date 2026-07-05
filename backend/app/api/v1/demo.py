from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import ApiContainerDependency
from app.api.v1.responses import DemoLoadFixturesResponse

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/load-fixtures", response_model=DemoLoadFixturesResponse)
def load_demo_fixtures(container: ApiContainerDependency) -> DemoLoadFixturesResponse:
    return container.load_canonical_demo()
