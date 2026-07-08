from __future__ import annotations

import logging

from app.llm.errors import LLMOutputParseError, LLMOutputValidationError
from app.llm.observability.events import LLMReliabilityEvent, LLMReliabilityEventType

_PARSE_ERROR_CODE = LLMOutputParseError.error_code
_VALIDATION_ERROR_CODE = LLMOutputValidationError.error_code
_FAILURE_EVENT_TYPES = (
    LLMReliabilityEventType.ATTEMPT_FAILED,
    LLMReliabilityEventType.RETRY_EXHAUSTED,
)


class CountingObserver:
    """In-memory counters + the schema-valid-rate instrument. No persistence,
    no external telemetry — per Rebuild-15's explicit observability-scope limit.
    """

    def __init__(self) -> None:
        self._counts_by_event_type: dict[str, int] = {}
        self._counts_by_error_code: dict[str, int] = {}
        self._succeeded_count = 0
        self._parse_failure_count = 0
        self._validation_failure_count = 0

    def record(self, event: LLMReliabilityEvent) -> None:
        event_type_value = event.event_type.value
        self._counts_by_event_type[event_type_value] = (
            self._counts_by_event_type.get(event_type_value, 0) + 1
        )
        if event.error_code is not None:
            self._counts_by_error_code[event.error_code] = (
                self._counts_by_error_code.get(event.error_code, 0) + 1
            )

        if event.event_type == LLMReliabilityEventType.SUCCEEDED:
            self._succeeded_count += 1
        elif event.event_type in _FAILURE_EVENT_TYPES:
            if event.error_code == _PARSE_ERROR_CODE:
                self._parse_failure_count += 1
            elif event.error_code == _VALIDATION_ERROR_CODE:
                self._validation_failure_count += 1

    def safe_summary(self) -> dict[str, object]:
        return {
            "counts_by_event_type": dict(self._counts_by_event_type),
            "counts_by_error_code": dict(self._counts_by_error_code),
            "schema_valid_rate": self._schema_valid_rate(),
        }

    def _schema_valid_rate(self) -> float | None:
        denominator = (
            self._succeeded_count + self._parse_failure_count + self._validation_failure_count
        )
        if denominator == 0:
            return None
        return self._succeeded_count / denominator


class LoggingObserver:
    """Emits one sanitized log record per event. Event fields are already
    redacted at construction (`LLMReliabilityEvent`), so no re-redaction is
    needed here — only avoid introducing any new, unredacted field.
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger("app.llm.reliability")

    def record(self, event: LLMReliabilityEvent) -> None:
        self._logger.info(
            "event_type=%s schema_name=%s attempt=%s max_attempts=%s "
            "error_code=%s provider=%s mode=%s reason_code=%s",
            event.event_type.value,
            event.schema_name,
            event.attempt,
            event.max_attempts,
            event.error_code,
            event.provider,
            event.mode,
            event.reason_code,
        )
