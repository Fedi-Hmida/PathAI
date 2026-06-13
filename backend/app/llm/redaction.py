from app.security.redaction import redact_text


def redact_for_llm(text: str) -> str:
    return redact_text(text)
