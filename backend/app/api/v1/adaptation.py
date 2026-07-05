from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.dependencies import AdaptationServiceDependency
from app.schemas.adaptation import AdaptationEventDTO
from app.schemas.ids import AdaptationId

router = APIRouter(prefix="/adaptations", tags=["adaptations"])


@router.get("/{adaptation_id}", response_model=AdaptationEventDTO)
def get_adaptation(
    adaptation_id: AdaptationId,
    service: AdaptationServiceDependency,
) -> AdaptationEventDTO:
    return service.get_by_id(adaptation_id)
