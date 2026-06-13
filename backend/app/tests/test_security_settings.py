from typing import Any, cast

from app.core.config import Settings


def build_settings_without_env(**overrides: object) -> Settings:
    settings_cls = cast(Any, Settings)
    return cast(Settings, settings_cls(_env_file=None, **overrides))


def test_security_settings_local_defaults_allow_development_workflow() -> None:
    settings = build_settings_without_env()

    assert settings.dev_endpoints_enabled is True
    assert settings.demo_endpoints_enabled is True
    assert settings.internal_errors_exposed is True
    assert settings.rate_limit_enabled is False
    assert "http://localhost:3000" in settings.allowed_origins


def test_security_settings_production_defaults_are_safer() -> None:
    settings = build_settings_without_env(app_env="production")

    assert settings.dev_endpoints_enabled is False
    assert settings.demo_endpoints_enabled is False
    assert settings.internal_errors_exposed is False


def test_allowed_origins_parse_comma_separated_env_value() -> None:
    settings = build_settings_without_env(
        allowed_origins="http://localhost:3000,https://demo.example.test"
    )

    assert settings.allowed_origins == [
        "http://localhost:3000",
        "https://demo.example.test",
    ]
