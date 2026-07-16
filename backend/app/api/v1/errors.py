from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.orchestration.assessment_agent_gateway import (
    AgentError,
    AssessmentQuestionMismatchError,
    AssessmentSessionNotActiveError,
    LLMGenerationUnavailableError,
)
from app.orchestration.workspace_generation_gateway import (
    AssessmentNotCompleteError,
)
from app.repositories.errors import DuplicateRecordError, NotFoundError, RepositoryError
from app.services.auth import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    TokenRejectedError,
)
from app.services.workspace import WorkspaceExistsError


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

    @app.exception_handler(WorkspaceExistsError)
    async def workspace_exists_handler(
        _request: Request,
        _error: WorkspaceExistsError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "workspace already exists"})

    @app.exception_handler(AssessmentSessionNotActiveError)
    async def assessment_session_not_active_handler(
        _request: Request,
        _error: AssessmentSessionNotActiveError,
    ) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "assessment session is not active"})

    @app.exception_handler(AssessmentQuestionMismatchError)
    async def assessment_question_mismatch_handler(
        _request: Request,
        _error: AssessmentQuestionMismatchError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "submitted answer does not match the current question"},
        )

    @app.exception_handler(LLMGenerationUnavailableError)
    async def llm_generation_unavailable_handler(
        _request: Request,
        error: LLMGenerationUnavailableError,
    ) -> JSONResponse:
        # A distinct, retry-oriented contract for an enabled LLM agent that
        # failed with no fallback active: the UI shows an explicit "generation
        # failed — retry" state instead of another topic's canned content.
        # Body carries no secrets or provider detail — only a stable code.
        return JSONResponse(
            status_code=503,
            content={
                "detail": "We couldn't generate this yet. Please retry.",
                "code": error.code,
            },
        )

    @app.exception_handler(AgentError)
    async def agent_error_handler(
        _request: Request,
        _error: AgentError,
    ) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": "agent execution failed"})

    @app.exception_handler(AssessmentNotCompleteError)
    async def assessment_not_complete_handler(
        _request: Request,
        _error: AssessmentNotCompleteError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "complete your diagnostic assessment first"},
        )

