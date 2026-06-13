from app.core.config import Settings, get_settings
from app.llm.types import SafeLLMConfig


def get_safe_llm_config(settings: Settings | None = None) -> SafeLLMConfig:
    active_settings = settings or get_settings()
    return SafeLLMConfig(
        api_url_configured=bool(active_settings.llm_api_url),
        api_key_configured=bool(active_settings.llm_api_key),
        model=active_settings.university_llm_model,
        timeout_seconds=active_settings.llm_timeout_seconds,
        max_retries=active_settings.llm_max_retries,
        retry_backoff_seconds=active_settings.llm_retry_backoff_seconds,
        mock_mode=active_settings.llm_mock_mode,
        prompt_version=active_settings.llm_prompt_version,
    )


def assert_real_llm_configured(settings: Settings | None = None) -> None:
    active_settings = settings or get_settings()
    if active_settings.llm_mock_mode:
        from app.llm.errors import LLMConfigurationError

        raise LLMConfigurationError("Real LLM calls are disabled while LLM_MOCK_MODE is true.")

    if not active_settings.llm_api_url or not active_settings.llm_api_key:
        from app.llm.errors import LLMConfigurationError

        raise LLMConfigurationError("University LLM API URL and API key must be configured.")
