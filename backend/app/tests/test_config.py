from typing import Any, cast

from app.core.config import Settings


def build_settings_without_env(**overrides: object) -> Settings:
    settings_cls = cast(Any, Settings)
    return cast(Settings, settings_cls(_env_file=None, **overrides))


def test_default_settings() -> None:
    settings = build_settings_without_env()

    assert settings.app_name == "PathAI API"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.mongodb_db_name == "pathai_dev"
    assert settings.mongodb_server_selection_timeout_ms == 1000
    assert settings.mongodb_connect_on_startup is True
