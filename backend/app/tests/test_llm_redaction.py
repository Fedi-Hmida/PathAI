from app.llm.redaction import redact_for_llm


def test_redact_for_llm_removes_sensitive_tokens() -> None:
    text = (
        "student@example.com user_id=665f1a000000000000000000 "
        "token=super-secret eyJabc.def.ghi"
    )

    redacted = redact_for_llm(text)

    assert "student@example.com" not in redacted
    assert "665f1a000000000000000000" not in redacted
    assert "super-secret" not in redacted
    assert "eyJabc.def.ghi" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
