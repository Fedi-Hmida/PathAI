from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.core.settings import Settings, get_settings

router = APIRouter(tags=["health"])
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.get("/health")
def health(settings: SettingsDependency) -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }


@router.get("/readiness")
def readiness(settings: SettingsDependency) -> dict[str, Any]:
    return {
        "status": "ready",
        "checks": settings.readiness_flags(),
    }
