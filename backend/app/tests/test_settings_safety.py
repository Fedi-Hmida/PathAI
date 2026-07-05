from pydantic import SecretStr

from app.core.logging import redact_mapping
from app.core.settings import Settings


def test_settings_redacts_secret_fields() -> None:
    settings = Settings(llm_api_key=SecretStr("not-a-real-key"))

    redacted = settings.redacted_dict()

    assert redacted["llm_api_key"] == "***REDACTED***"
    assert "not-a-real-key" not in repr(settings)


def test_readiness_flags_do_not_include_secret_values() -> None:
    settings = Settings(
        llm_provider="university",
        openai_base_url="https://example.invalid",
        university_llm_model="demo-model",
        openai_api_key=SecretStr("not-a-real-key"),
        llm_mock_mode=False,
    )

    flags = settings.readiness_flags()
    rendered = str(flags)

    assert flags["llm_configured"] is True
    assert "not-a-real-key" not in rendered
    assert "https://example.invalid" not in rendered


def test_redact_mapping_masks_sensitive_keys() -> None:
    redacted = redact_mapping({"api_key": "not-a-real-key", "safe": "visible"})

    assert redacted == {"api_key": "***REDACTED***", "safe": "visible"}
