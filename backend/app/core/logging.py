import logging
from collections.abc import Mapping
from typing import Any

SENSITIVE_TOKENS = ("secret", "token", "key", "password", "authorization", "cookie", "uri")


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def redact_mapping(values: Mapping[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in values.items():
        if _is_sensitive_key(key):
            redacted[key] = "***REDACTED***" if value else ""
        else:
            redacted[key] = value
    return redacted


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in SENSITIVE_TOKENS)

