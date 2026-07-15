from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.llm.redaction import redact_secrets


class LLMReliabilityEventType(StrEnum):
    ATTEMPT_STARTED = "attempt_started"
    ATTEMPT_FAILED = "attempt_failed"
    RETRY_EXHAUSTED = "retry_exhausted"
    FALLBACK_USED = "fallback_used"
    GENERATION_UNAVAILABLE = "generation_unavailable"
    SUCCEEDED = "succeeded"
    RUN_BUDGET_EXHAUSTED = "run_budget_exhausted"


_REDACTED_FIELDS = ("error_code", "provider", "mode", "reason_code")


class LLMReliabilityEvent(BaseModel):
    """A sanitized, bounded signal about one LLM call attempt or outcome.

    Deliberately has no `prompt`, `raw_text`, or raw-exception field — this
    model must stay safe to log unconditionally, so it never carries content
    that could contain user input, model output, or secrets.
    """

    model_config = ConfigDict(frozen=True)

    event_type: LLMReliabilityEventType
    schema_name: str = Field(min_length=1, max_length=160)
    attempt: int = Field(ge=1, le=10)
    max_attempts: int = Field(ge=1, le=10)
    error_code: str | None = Field(default=None, max_length=80)
    provider: str | None = Field(default=None, max_length=80)
    mode: str | None = Field(default=None, max_length=40)
    reason_code: str | None = Field(default=None, max_length=120)

    @field_validator(*_REDACTED_FIELDS, mode="before")
    @classmethod
    def _redact_before_validation(cls, value: object) -> object:
        if value is None:
            return None
        return redact_secrets(value)
