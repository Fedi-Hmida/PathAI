from typing import Any

import certifi
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.models import DOCUMENT_MODELS
from app.security.redaction import redact_text

logger = get_logger(__name__)


class MongoDBManager:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient[Any] | None = None
        self.database: AsyncIOMotorDatabase[Any] | None = None
        self.initialized: bool = False
        self.last_error: str | None = None

    async def connect(self, settings: Settings | None = None) -> None:
        active_settings = settings or get_settings()
        self.client = AsyncIOMotorClient(
            active_settings.mongodb_uri,
            **_mongodb_client_options(active_settings),
        )
        self.database = self.client[active_settings.mongodb_db_name]

        if not await self.ping():
            raise ConnectionError(self.last_error or "MongoDB ping failed")

        from beanie import init_beanie

        await init_beanie(database=self.database, document_models=DOCUMENT_MODELS)  # type: ignore[arg-type]
        self.initialized = True
        self.last_error = None
        logger.info("MongoDB connected database=%s", active_settings.mongodb_db_name)

    async def ready(self, settings: Settings | None = None) -> bool:
        if self.client is None or self.database is None:
            try:
                await self.connect(settings=settings)
            except Exception as exc:
                self.last_error = redact_text(str(exc))
                return False
            return True

        if not await self.ping():
            return False

        if not self.initialized:
            try:
                from beanie import init_beanie

                await init_beanie(
                    database=self.database,  # type: ignore[arg-type]
                    document_models=DOCUMENT_MODELS,
                )
            except Exception as exc:
                self.last_error = redact_text(str(exc))
                logger.warning("Beanie initialization failed error=%s", self.last_error)
                return False
            self.initialized = True

        return True

    async def ping(self) -> bool:
        if self.client is None:
            self.last_error = "MongoDB client is not initialized"
            return False

        try:
            await self.client.admin.command("ping")
        except PyMongoError as exc:
            self.last_error = redact_text(str(exc))
            logger.warning("MongoDB ping failed error=%s", self.last_error)
            return False

        self.last_error = None
        return True

    async def close(self) -> None:
        if self.client is not None:
            self.client.close()
            logger.info("MongoDB client closed")
        self.client = None
        self.database = None
        self.initialized = False


database_manager = MongoDBManager()


def get_database() -> AsyncIOMotorDatabase[Any]:
    if database_manager.database is None:
        raise RuntimeError("MongoDB database is not initialized")
    return database_manager.database


def _mongodb_client_options(settings: Settings) -> dict[str, Any]:
    options: dict[str, Any] = {
        "serverSelectionTimeoutMS": settings.mongodb_server_selection_timeout_ms,
    }
    uri = settings.mongodb_uri.lower()
    if uri.startswith("mongodb+srv://") or ".mongodb.net" in uri:
        options["tlsCAFile"] = certifi.where()
    return options
