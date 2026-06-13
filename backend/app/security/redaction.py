import re
from collections.abc import Mapping, Sequence

from app.security.constants import (
    REDACTED_EMAIL,
    REDACTED_ID,
    REDACTED_SECRET,
    REDACTED_TOKEN,
    REDACTED_TRACE_CONTENT,
    SENSITIVE_KEY_PARTS,
    TRACE_CONTENT_KEY_PARTS,
)

EMAIL_RE = re.compile(r"[\w.\-+]+@[\w.\-]+\.\w+")
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b")
OBJECT_ID_RE = re.compile(r"\b[a-fA-F0-9]{24}\b")
BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]+")
MONGODB_URI_RE = re.compile(r"mongodb(?:\+srv)?://[^\s'\"<>]+", re.IGNORECASE)
MONGODB_ATLAS_HOST_RE = re.compile(r"\b[a-z0-9.-]+\.mongodb\.net(?::\d+)?\b", re.IGNORECASE)
KEY_VALUE_SECRET_RE = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*['\"]?[^'\"\s,;]+"
)


def redact_text(text: str) -> str:
    redacted = EMAIL_RE.sub(REDACTED_EMAIL, text)
    redacted = MONGODB_URI_RE.sub(REDACTED_SECRET, redacted)
    redacted = MONGODB_ATLAS_HOST_RE.sub(REDACTED_SECRET, redacted)
    redacted = JWT_RE.sub(REDACTED_TOKEN, redacted)
    redacted = BEARER_RE.sub(f"Bearer {REDACTED_TOKEN}", redacted)
    redacted = OBJECT_ID_RE.sub(REDACTED_ID, redacted)
    return KEY_VALUE_SECRET_RE.sub(lambda match: f"{match.group(1)}={REDACTED_SECRET}", redacted)


def redact_value(value: object, key_hint: str | None = None) -> object:
    if key_hint and _is_sensitive_key(key_hint):
        return REDACTED_SECRET
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        return {
            str(key): redact_value(item, str(key))
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [redact_value(item) for item in value]
    return value


def redact_mapping(metadata: Mapping[str, object]) -> dict[str, object]:
    return {str(key): redact_value(value, str(key)) for key, value in metadata.items()}


def sanitize_trace_metadata(
    metadata: Mapping[str, object],
    privacy_mode: str = "strict",
) -> dict[str, object]:
    if privacy_mode == "disabled":
        return {}
    sanitized: dict[str, object] = {}
    for key, value in metadata.items():
        key_text = str(key)
        if privacy_mode == "strict" and _is_trace_content_key(key_text):
            sanitized[key_text] = REDACTED_TRACE_CONTENT
            continue
        sanitized[key_text] = redact_value(value, key_text)
    return sanitized


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def _is_trace_content_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in TRACE_CONTENT_KEY_PARTS)
