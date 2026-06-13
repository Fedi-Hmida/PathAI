from fastapi import APIRouter

from app.adapter.errors import AdapterError
from app.adapter.schemas import (
    AdaptationCheckRequest,
    AdaptationDecision,
    AdaptationHistoryResponse,
    AdaptationReplanRequest,
    AdaptationResult,
)
from app.adapter.service import AdapterService
from app.core.errors import PathAIError

router = APIRouter(prefix="/adapt", tags=["adaptation"])
adapter_service = AdapterService()


@router.post(
    "/check",
    response_model=AdaptationDecision,
    summary="Analyze progress and quiz signals without running replanning.",
)
async def check_adaptation(request: AdaptationCheckRequest) -> AdaptationDecision:
    try:
        return adapter_service.check_adaptation(request)
    except AdapterError as exc:
        raise _to_pathai_error(exc) from exc


@router.post(
    "/replan",
    response_model=AdaptationResult,
    summary="Run the deterministic manual adaptation/replanning pipeline.",
)
async def replan_adaptation(request: AdaptationReplanRequest) -> AdaptationResult:
    try:
        return await adapter_service.run_replan(request)
    except AdapterError as exc:
        raise _to_pathai_error(exc) from exc


@router.get(
    "/{curriculum_id}/history",
    response_model=AdaptationHistoryResponse,
    summary="Return temporary no-auth adaptation history for a curriculum.",
)
async def get_adaptation_history(curriculum_id: str) -> AdaptationHistoryResponse:
    return adapter_service.get_history(curriculum_id)


@router.get(
    "/{adaptation_id}",
    response_model=AdaptationResult,
    summary="Return a temporary no-auth adaptation result by ID.",
)
async def get_adaptation(adaptation_id: str) -> AdaptationResult:
    try:
        return adapter_service.get_adaptation(adaptation_id)
    except AdapterError as exc:
        raise _to_pathai_error(exc) from exc


def _to_pathai_error(exc: AdapterError) -> PathAIError:
    return PathAIError(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
    )
