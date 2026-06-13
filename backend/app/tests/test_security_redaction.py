from app.security.redaction import redact_mapping, redact_text, sanitize_trace_metadata


def test_redact_text_removes_common_secret_and_pii_patterns() -> None:
    text = (
        "email learner@example.test api_key=abc123 "
        "Authorization=Bearer aaa.bbb.ccc mongodb://user:pass@localhost/pathai "
        "object 665f1a000000000000000000"
    )

    redacted = redact_text(text)

    assert "learner@example.test" not in redacted
    assert "abc123" not in redacted
    assert "user:pass" not in redacted
    assert "665f1a000000000000000000" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_SECRET]" in redacted
    assert "[REDACTED_ID]" in redacted


def test_redact_text_removes_mongodb_atlas_hosts() -> None:
    text = "MongoDB ping failed for cluster-shard-00-00.example.mongodb.net:27017"

    redacted = redact_text(text)

    assert "example.mongodb.net" not in redacted
    assert "[REDACTED_SECRET]" in redacted


def test_redact_mapping_redacts_sensitive_keys_recursively() -> None:
    metadata = {
        "api_key": "abc123",
        "nested": {"token": "demo-token", "safe": "ok"},
    }

    redacted = redact_mapping(metadata)

    assert redacted["api_key"] == "[REDACTED_SECRET]"
    nested = redacted["nested"]
    assert isinstance(nested, dict)
    assert nested["token"] == "[REDACTED_SECRET]"
    assert nested["safe"] == "ok"


def test_sanitize_trace_metadata_strict_removes_raw_prompt_content() -> None:
    metadata = {
        "prompt": "student email learner@example.test and secret=abc123",
        "goal": "Learn RAG",
        "trace_id": "665f1a000000000000000000",
    }

    sanitized = sanitize_trace_metadata(metadata, privacy_mode="strict")

    assert sanitized["prompt"] == "[REDACTED_TRACE_CONTENT]"
    assert sanitized["goal"] == "Learn RAG"
    assert sanitized["trace_id"] == "[REDACTED_ID]"


def test_sanitize_trace_metadata_disabled_returns_empty_metadata() -> None:
    assert sanitize_trace_metadata({"goal": "Learn RAG"}, privacy_mode="disabled") == {}
