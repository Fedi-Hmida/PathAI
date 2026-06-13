from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.db.mongodb import database_manager
from app.security.middleware import SecurityHardeningMiddleware, cors_origins_for_settings
from app.security.redaction import redact_text

logger = get_logger(__name__)


def build_lifespan(
    app_settings: Settings,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        configure_logging(app_settings.log_level)
        app.state.settings = app_settings
        logger.info("Starting %s in %s mode", app_settings.app_name, app_settings.app_env)
        if app_settings.mongodb_connect_on_startup:
            try:
                await database_manager.connect(settings=app_settings)
                app.state.mongodb_ready = True
            except Exception as exc:
                app.state.mongodb_ready = False
                logger.warning("MongoDB unavailable during startup error=%s", redact_text(str(exc)))
        yield
        await database_manager.close()
        logger.info("Stopping %s", app_settings.app_name)

    return lifespan


def create_app(app_settings: Settings | None = None) -> FastAPI:
    resolved_settings = app_settings or get_settings()
    app = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        docs_url="/docs" if resolved_settings.enable_docs else None,
        redoc_url="/redoc" if resolved_settings.enable_docs else None,
        openapi_url="/openapi.json" if resolved_settings.enable_docs else None,
        lifespan=build_lifespan(resolved_settings),
    )
    app.state.settings = resolved_settings
    register_exception_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins_for_settings(resolved_settings),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHardeningMiddleware, settings=resolved_settings)
    app.include_router(api_router, prefix=resolved_settings.api_v1_prefix)
    return app


app = create_app()
