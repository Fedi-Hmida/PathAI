from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.common import ErrorPayload, ErrorResponse
from app.security.redaction import redact_mapping, redact_text

logger = get_logger(__name__)


class PathAIError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, object] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


def build_error_response(
    code: str,
    message: str,
    status_code: int,
    details: dict[str, object] | None = None,
) -> JSONResponse:
    settings = get_settings()
    public_details = redact_mapping(details or {}) if settings.redact_log_values else details or {}
    payload = ErrorResponse(
        error=ErrorPayload(code=code, message=message, details=public_details)
    )
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PathAIError)
    async def pathai_error_handler(_request: Request, exc: PathAIError) -> JSONResponse:
        return build_error_response(
            code=exc.code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return build_error_response(
            code="validation_error",
            message="Request validation failed.",
            status_code=422,
            details={"errors": exc.errors()},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error."
        return build_error_response(
            code="http_error",
            message=message,
            status_code=exc.status_code,
            details={},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        settings = getattr(request.app.state, "settings", get_settings())
        request_id = getattr(request.state, "request_id", None)
        logger.exception(
            "Unhandled request error request_id=%s error=%s",
            request_id,
            redact_text(str(exc)),
        )
        details: dict[str, Any] = {"request_id": request_id} if request_id else {}
        if settings.internal_errors_exposed:
            details["exception_type"] = exc.__class__.__name__
        return build_error_response(
            code="internal_error",
            message=str(exc) if settings.internal_errors_exposed else "Internal server error.",
            status_code=500,
            details=details,
        )
