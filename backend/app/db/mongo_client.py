from __future__ import annotations

from typing import Any

import pymongo

from app.core.settings import Settings

_SERVER_SELECTION_TIMEOUT_MS = 5000


class MongoNotConfiguredError(RuntimeError):
    """Raised when a MongoDB operation is requested without a configured URI."""


def build_mongo_client_from_settings(settings: Settings) -> pymongo.MongoClient[Any]:
    if not settings.mongodb_uri:
        raise MongoNotConfiguredError("MongoDB URI is not configured.")
    return pymongo.MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=_SERVER_SELECTION_TIMEOUT_MS,
    )


def ping_mongo_from_settings(settings: Settings) -> bool:
    client = build_mongo_client_from_settings(settings)
    try:
        client[settings.mongodb_database_name].command("ping")
        return True
    finally:
        client.close()
