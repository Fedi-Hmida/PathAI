from __future__ import annotations

from app.llm.redaction import redact_secrets


class LLMError(RuntimeError):
    error_code = "llm_error"
    retryable = False

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        retryable: bool | None = None,
    ) -> None:
        self.provider = provider
        if retryable is not None:
            self.retryable = retryable
        self.safe_message = redact_secrets(message)
        super().__init__(self.safe_message)

    def to_safe_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "error_code": self.error_code,
            "message": self.safe_message,
            "retryable": self.retryable,
        }
        if self.provider:
            payload["provider"] = self.provider
        return payload


class LLMProviderError(LLMError):
    error_code = "llm_provider_error"
    retryable = True


class LLMTimeoutError(LLMError):
    error_code = "llm_timeout"
    retryable = True


class LLMStructuredOutputError(LLMError):
    error_code = "llm_structured_output_error"
    retryable = False


class LLMOutputParseError(LLMStructuredOutputError):
    error_code = "llm_output_parse_error"


class LLMOutputValidationError(LLMStructuredOutputError):
    error_code = "llm_output_validation_error"


class LLMRetryLimitExceeded(LLMError):
    error_code = "llm_retry_limit_exceeded"
    retryable = False


class LLMRunBudgetExhaustedError(LLMError):
    error_code = "llm_run_budget_exhausted"
    retryable = False
