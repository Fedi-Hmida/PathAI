from typing import Final

DEV_PATH_PREFIX: Final[str] = "/dev"
PUBLIC_API_PATHS: Final[set[str]] = {"/health", "/ready"}
REDACTED_SECRET: Final[str] = "[REDACTED_SECRET]"
REDACTED_EMAIL: Final[str] = "[REDACTED_EMAIL]"
REDACTED_TOKEN: Final[str] = "[REDACTED_TOKEN]"
REDACTED_ID: Final[str] = "[REDACTED_ID]"
REDACTED_TRACE_CONTENT: Final[str] = "[REDACTED_TRACE_CONTENT]"

SENSITIVE_KEY_PARTS: Final[tuple[str, ...]] = (
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "credential",
    "jwt",
    "key",
    "mongodb_uri",
    "password",
    "secret",
    "token",
)

TRACE_CONTENT_KEY_PARTS: Final[tuple[str, ...]] = (
    "completion",
    "context",
    "llm_input",
    "message",
    "messages",
    "prompt",
    "raw_response",
    "resource_content",
    "student_answer",
)
