from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.db.mongodb import database_manager
from app.schemas.health import HealthResponse, ReadinessResponse
from app.security.redaction import redact_text

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessResponse}},
)
async def readiness_check() -> ReadinessResponse | JSONResponse:
    settings = get_settings()
    database_ready = await database_manager.ready(settings=settings)
    checks = {
        "api": "ok",
        "mongodb": "ok" if database_ready else "unavailable",
    }
    payload = ReadinessResponse(
        status="ready" if database_ready else "not_ready",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        checks=checks,
        message=None if database_ready else _safe_readiness_message(database_manager.last_error),
    )

    if database_ready:
        return payload

    return JSONResponse(status_code=503, content=jsonable_encoder(payload))


def _safe_readiness_message(message: str | None) -> str | None:
    if message is None:
        return None
    return redact_text(message)
