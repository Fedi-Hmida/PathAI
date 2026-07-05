from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.repositories.errors import DuplicateRecordError, NotFoundError, RepositoryError


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
