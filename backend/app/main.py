from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.errors import register_api_exception_handlers
from app.api.v1.router import api_router
from app.core.logging import configure_logging
from app.core.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging()

    app = FastAPI(
        title=resolved_settings.app_name,
        debug=resolved_settings.app_debug,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )
    register_api_exception_handlers(app)
    app.include_router(api_router, prefix=resolved_settings.api_v1_prefix)
    return app


app = create_app()
