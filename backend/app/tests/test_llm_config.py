from typing import Any, cast

from app.core.config import Settings
from app.llm.config import get_safe_llm_config


def build_settings_without_env(**overrides: object) -> Settings:
    settings_cls = cast(Any, Settings)
    return cast(Settings, settings_cls(_env_file=None, **overrides))


def test_llm_settings_defaults() -> None:
    settings = build_settings_without_env()

    assert settings.university_llm_model == "pathai-university-default"
    assert settings.llm_timeout_seconds == 30.0
    assert settings.llm_max_retries == 2
    assert settings.llm_retry_backoff_seconds == 0.5
    assert settings.llm_mock_mode is True
    assert settings.llm_prompt_version == "v1"


def test_safe_llm_config_never_exposes_api_key() -> None:
    settings = build_settings_without_env(
        university_llm_api_url="https://llm.example.edu/chat",
        university_llm_api_key="secret-key",
        university_llm_model="demo-model",
    )

    safe_config = get_safe_llm_config(settings)
    dumped = safe_config.model_dump()

    assert safe_config.api_url_configured is True
    assert safe_config.api_key_configured is True
    assert safe_config.model == "demo-model"
    assert "secret-key" not in str(dumped)
    assert "api_key" not in dumped


def test_openai_compatible_llm_aliases() -> None:
    settings = build_settings_without_env(
        openai_base_url="https://llm.example.edu/api/",
        openai_api_key="secret-key",
    )

    assert settings.llm_api_url == "https://llm.example.edu/api/chat/completions"
    assert settings.llm_api_key == "secret-key"
