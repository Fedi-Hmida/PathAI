from __future__ import annotations

import re

REDACTED = "[REDACTED]"

_BEARER_PATTERN = re.compile(
    r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}",
    flags=re.IGNORECASE,
)
_MONGODB_URI_PATTERN = re.compile(
    r"mongodb(?:\+srv)?://[^\s\"')]+",
    flags=re.IGNORECASE,
)
_KEY_VALUE_PATTERN = re.compile(
    r"\b(api[_-]?key|token|secret|password)\s*[:=]\s*([^\s,;]+)",
    flags=re.IGNORECASE,
)
_LONG_SECRET_PATTERN = re.compile(r"\b[A-Za-z0-9_\-]{32,}\b")


def redact_secrets(value: object) -> str:
    text = str(value)
    text = _BEARER_PATTERN.sub(f"Bearer {REDACTED}", text)
    text = _MONGODB_URI_PATTERN.sub("[REDACTED_MONGODB_URI]", text)
    text = _KEY_VALUE_PATTERN.sub(lambda match: f"{match.group(1)}={REDACTED}", text)
    return _LONG_SECRET_PATTERN.sub(REDACTED, text)
