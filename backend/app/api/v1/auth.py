from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.v1.dependencies import (
    AuthServiceDependency,
    CurrentUserDependency,
    SettingsDependency,
    require_auth_enabled,
)
from app.core.settings import Settings
from app.schemas.auth import AuthConfig, AuthSessionResponse, LoginRequest, UserCreate, UserDTO
from app.services.auth import TokenRejectedError

# Deliberately NOT gated by require_auth_enabled: callers must be able to
# tell whether auth is on before they know whether to call any gated route.
public_router = APIRouter(prefix="/auth", tags=["auth"])


@public_router.get("/config", response_model=AuthConfig)
def get_auth_config(settings: SettingsDependency) -> AuthConfig:
    return AuthConfig(enabled=settings.enable_auth)


# Every other auth route is hidden (404) unless PATHAI_ENABLE_AUTH is set.
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    dependencies=[Depends(require_auth_enabled)],
)


@router.post("/register", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    response: Response,
    settings: SettingsDependency,
    service: AuthServiceDependency,
) -> AuthSessionResponse:
    user = service.register(payload)
    return _start_session(response, settings, service, user)


@router.post("/login", response_model=AuthSessionResponse)
def login(
    payload: LoginRequest,
    response: Response,
    settings: SettingsDependency,
    service: AuthServiceDependency,
) -> AuthSessionResponse:
    user = service.authenticate(payload).to_public()
    return _start_session(response, settings, service, user)


@router.post("/refresh", response_model=AuthSessionResponse)
def refresh(
    request: Request,
    response: Response,
    settings: SettingsDependency,
    service: AuthServiceDependency,
) -> AuthSessionResponse:
    token = request.cookies.get(settings.refresh_cookie_name)
    if not token:
        raise TokenRejectedError
    body, refresh_token = service.rotate_session(token)
    _set_refresh_cookie(response, settings, refresh_token)
    return body


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    settings: SettingsDependency,
    service: AuthServiceDependency,
) -> None:
    service.logout(request.cookies.get(settings.refresh_cookie_name))
    _clear_refresh_cookie(response, settings)


@router.get("/me", response_model=UserDTO)
def me(user: CurrentUserDependency) -> UserDTO:
    return user


def _start_session(
    response: Response,
    settings: Settings,
    service: AuthServiceDependency,
    user: UserDTO,
) -> AuthSessionResponse:
    body, refresh_token = service.issue_session(user)
    _set_refresh_cookie(response, settings, refresh_token)
    return body


def _cookie_path(settings: Settings) -> str:
    return f"{settings.api_v1_prefix}/auth"


def _set_refresh_cookie(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        max_age=settings.refresh_token_ttl_seconds,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,  # type: ignore[arg-type]
        path=_cookie_path(settings),
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,  # type: ignore[arg-type]
        path=_cookie_path(settings),
    )
