from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import Settings
from app.core.logging import get_logger
from app.schemas.common import ErrorPayload, ErrorResponse
from app.security.audit import audit_event_to_log_extra, build_audit_event
from app.security.guards import should_block_demo_path, should_block_dev_path
from app.security.rate_limit import InMemoryRateLimiter
from app.security.redaction import redact_text
from app.security.settings import effective_allowed_origins

logger = get_logger(__name__)


class SecurityHardeningMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings
        self.rate_limiter = InMemoryRateLimiter(settings.rate_limit_requests_per_minute)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id") or f"req_{uuid4().hex}"
        request.state.request_id = request_id

        gated_response = self._gate_request(request)
        if gated_response is not None:
            self._decorate_response(gated_response, request_id)
            self._audit(request, gated_response.status_code, request_id)
            return gated_response

        rate_limit_response = self._rate_limit(request, request_id)
        if rate_limit_response is not None:
            self._decorate_response(rate_limit_response, request_id)
            self._audit(request, rate_limit_response.status_code, request_id)
            return rate_limit_response

        try:
            response = await call_next(request)
        except Exception as exc:
            self._audit(request, 500, request_id, {"error": redact_text(str(exc))})
            raise

        self._decorate_response(response, request_id)
        self._audit(request, response.status_code, request_id)
        return response

    def _gate_request(self, request: Request) -> JSONResponse | None:
        path = request.url.path
        if should_block_dev_path(path, self.settings):
            return _error_response(
                status_code=404,
                code="dev_endpoints_disabled",
                message="Development endpoint is disabled.",
            )
        if should_block_demo_path(path, self.settings):
            return _error_response(
                status_code=403,
                code="demo_endpoints_disabled",
                message="Temporary demo endpoint is disabled.",
            )
        return None

    def _rate_limit(self, request: Request, request_id: str) -> JSONResponse | None:
        if not self.settings.rate_limit_enabled:
            return None
        client_host = request.client.host if request.client else "unknown"
        key = f"{client_host}:{request.url.path}"
        result = self.rate_limiter.check(key)
        if result.allowed:
            return None
        response = _error_response(
            status_code=429,
            code="rate_limit_exceeded",
            message="Too many requests. Try again later.",
        )
        response.headers["Retry-After"] = str(result.retry_after_seconds)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-Request-ID"] = request_id
        return response

    def _decorate_response(self, response: Response, request_id: str) -> None:
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"

    def _audit(
        self,
        request: Request,
        status_code: int,
        request_id: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        if not self.settings.audit_log_enabled:
            return
        event = build_audit_event(
            event_type="http_request",
            request_id=request_id,
            route=request.url.path,
            method=request.method,
            status_code=status_code,
            metadata=metadata or {"query": str(request.url.query)},
            timestamp=request.state.audit_timestamp
            if hasattr(request.state, "audit_timestamp")
            else datetime.now(UTC),
        )
        logger.info("audit_event", extra=audit_event_to_log_extra(event))


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=ErrorPayload(code=code, message=message, details={})
        ).model_dump(mode="json"),
    )


def cors_origins_for_settings(settings: Settings) -> list[str]:
    return effective_allowed_origins(settings)
