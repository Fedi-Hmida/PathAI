from __future__ import annotations

from pathlib import Path

import pytest

from app.core.settings import Settings
from app.db.mongo_client import MongoNotConfiguredError, build_mongo_client_from_settings

APP_DIR = Path(__file__).resolve().parents[1]
BOUNDARY_DIRS = ("repositories", "agents", "api", "orchestration")
ALLOWED_APP_DB_CONSUMERS = (APP_DIR / "repositories" / "factory.py",)


def test_build_mongo_client_raises_when_unconfigured() -> None:
    settings = Settings(mongodb_uri="")
    with pytest.raises(MongoNotConfiguredError):
        build_mongo_client_from_settings(settings)


def test_mongodb_uri_defaults_to_empty_string() -> None:
    assert Settings().mongodb_uri == ""
    assert Settings().mongodb_database_name == "pathai"


def test_mongodb_uri_is_redacted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MONGODB_URI", "mongodb+srv://user:pass@cluster.example.net/db")
    settings = Settings()
    redacted = settings.redacted_dict()
    assert redacted["mongodb_uri"] == "***REDACTED***"


def test_mongodb_uri_redacts_to_empty_when_unset() -> None:
    settings = Settings(mongodb_uri="")
    assert settings.redacted_dict()["mongodb_uri"] == ""


@pytest.mark.parametrize("boundary_dir", BOUNDARY_DIRS)
def test_app_db_is_only_imported_by_the_repository_factory(boundary_dir: str) -> None:
    directory = APP_DIR / boundary_dir
    for path in directory.rglob("*.py"):
        if path in ALLOWED_APP_DB_CONSUMERS:
            continue
        text = path.read_text(encoding="utf-8")
        assert "app.db" not in text, (
            f"{path} references app.db outside the one allowlisted repository factory"
        )


def test_repository_factory_actually_imports_app_db() -> None:
    factory_path = APP_DIR / "repositories" / "factory.py"
    text = factory_path.read_text(encoding="utf-8")
    assert "app.db.mongo_client" in text
