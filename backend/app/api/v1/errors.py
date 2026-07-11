from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.repositories.errors import DuplicateRecordError, NotFoundError, RepositoryError
from app.services.auth import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    TokenRejectedError,
)


def register_api_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(
        _request: Request,
        _error: NotFoundError,
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "resource not found"})

    @app.exception_handler(DuplicateRecordError)
    async def duplicate_record_handler(
        _request: Request,
        _error: DuplicateRecordError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "resource already exists"})

    @app.exception_handler(RepositoryError)
    async def repository_error_handler(
        _request: Request,
        _error: RepositoryError,
    ) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "repository boundary error"})

    @app.exception_handler(EmailAlreadyRegisteredError)
    async def email_already_registered_handler(
        _request: Request,
        _error: EmailAlreadyRegisteredError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "email already registered"})

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(
        _request: Request,
        _error: InvalidCredentialsError,
    ) -> JSONResponse:
        # Deliberately identical to the token-rejected message: neither
        # response may reveal whether an email exists or a password matched.
        return JSONResponse(status_code=401, content={"detail": "invalid email or password"})

    @app.exception_handler(TokenRejectedError)
    async def token_rejected_handler(
        _request: Request,
        _error: TokenRejectedError,
    ) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": "authentication required"})
