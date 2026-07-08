from __future__ import annotations

import pytest
from pydantic import SecretStr

from app.core.settings import Settings
from app.llm.errors import LLMProviderError
from app.llm.live_client import (
    LIVE_LLM_OPT_IN_ENV_VAR,
    LiveLLMNotConfiguredError,
    LiveLLMSmokeResponse,
    OpenAICompatibleLiveLLMClient,
    build_live_client_from_settings,
    live_llm_smoke_enabled,
)
from app.llm.structured_output import parse_structured_output


def test_live_smoke_opt_in_guard_defaults_to_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(LIVE_LLM_OPT_IN_ENV_VAR, raising=False)

    assert live_llm_smoke_enabled() is False

    monkeypatch.setenv(LIVE_LLM_OPT_IN_ENV_VAR, "1")

    assert live_llm_smoke_enabled() is True


def test_missing_live_config_raises_without_secret_values() -> None:
    settings = Settings(llm_provider="mock")

    with pytest.raises(LiveLLMNotConfiguredError) as exc_info:
        build_live_client_from_settings(settings)

    assert "provider" in str(exc_info.value).lower()


def test_live_client_repr_does_not_expose_secret() -> None:
    client = OpenAICompatibleLiveLLMClient(
        provider="openai_compatible",
        model="tiny-json-model",
        base_url="https://example.invalid/v1",
        api_key=SecretStr("super-secret-api-key-value"),
    )

    assert "super-secret-api-key-value" not in repr(client)
    assert "example.invalid" not in repr(client)


def test_live_smoke_schema_uses_rebuild_12a_parser() -> None:
    result = parse_structured_output(
        '{"status":"ok","message":"live boundary parser check"}',
        LiveLLMSmokeResponse,
    )

    assert result.status == "ok"


def test_provider_error_message_is_sanitized() -> None:
    error = LLMProviderError(
        "provider failed with Bearer fake-token-value-1234567890",
        provider="openai_compatible",
    )

    assert "fake-token-value" not in str(error.to_safe_dict())
