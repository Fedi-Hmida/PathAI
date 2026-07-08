from __future__ import annotations

from app.llm import LLMProviderError, redact_secrets


def test_redaction_masks_secret_like_values() -> None:
    raw = (
        "Authorization: Bearer fake-token-value-1234567890 "
        "api_key=fake-key-value-1234567890 "
        "mongodb://user:password@example.invalid/path "
        "abcdefghijklmnopqrstuvwxyzABCDEF123456"
    )

    redacted = redact_secrets(raw)

    assert "fake-token-value" not in redacted
    assert "fake-key-value" not in redacted
    assert "password@example" not in redacted
    assert "abcdefghijklmnopqrstuvwxyzABCDEF123456" not in redacted
    assert "[REDACTED" in redacted


def test_llm_errors_expose_sanitized_messages_only() -> None:
    error = LLMProviderError(
        "provider failed with token=fake-secret-token-1234567890",
        provider="fake",
    )

    safe = error.to_safe_dict()

    assert "fake-secret-token" not in str(safe)
    assert safe["error_code"] == "llm_provider_error"
    assert safe["provider"] == "fake"
