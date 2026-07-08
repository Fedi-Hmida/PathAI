from __future__ import annotations

import logging

import pytest

from app.llm.observability import (
    CountingObserver,
    LLMReliabilityEvent,
    LLMReliabilityEventType,
    LoggingObserver,
    NullObserver,
)

_SECRET = "Bearer sk-fake-secret-token-1234567890"


def _event(**overrides: object) -> LLMReliabilityEvent:
    fields: dict[str, object] = {
        "event_type": LLMReliabilityEventType.SUCCEEDED,
        "schema_name": "KnowledgeMapAgentOutput",
        "attempt": 1,
        "max_attempts": 2,
    }
    fields.update(overrides)
    return LLMReliabilityEvent(**fields)


def test_reason_code_is_redacted_at_construction() -> None:
    event = _event(reason_code=_SECRET)

    assert event.reason_code is not None
    assert _SECRET not in event.reason_code
    assert _SECRET not in event.model_dump_json()


def test_error_code_is_redacted_at_construction() -> None:
    event = _event(error_code=_SECRET)

    assert event.error_code is not None
    assert _SECRET not in event.error_code
    assert _SECRET not in event.model_dump_json()


def test_provider_is_redacted_at_construction() -> None:
    event = _event(provider=_SECRET)

    assert event.provider is not None
    assert _SECRET not in event.provider
    assert _SECRET not in event.model_dump_json()


def test_schema_valid_rate_is_none_with_no_events() -> None:
    observer = CountingObserver()

    summary = observer.safe_summary()

    assert summary["schema_valid_rate"] is None


def test_schema_valid_rate_is_one_when_all_succeeded() -> None:
    observer = CountingObserver()
    for _ in range(3):
        observer.record(_event(event_type=LLMReliabilityEventType.SUCCEEDED))

    summary = observer.safe_summary()

    assert summary["schema_valid_rate"] == 1.0


def test_schema_valid_rate_mixed_and_raw_counts() -> None:
    observer = CountingObserver()
    observer.record(_event(event_type=LLMReliabilityEventType.SUCCEEDED))
    observer.record(_event(event_type=LLMReliabilityEventType.SUCCEEDED))
    observer.record(
        _event(
            event_type=LLMReliabilityEventType.ATTEMPT_FAILED,
            error_code="llm_output_parse_error",
        ),
    )
    observer.record(
        _event(
            event_type=LLMReliabilityEventType.RETRY_EXHAUSTED,
            error_code="llm_output_validation_error",
        ),
    )

    summary = observer.safe_summary()

    assert summary["schema_valid_rate"] == 0.5
    assert summary["counts_by_event_type"] == {
        "succeeded": 2,
        "attempt_failed": 1,
        "retry_exhausted": 1,
    }
    assert summary["counts_by_error_code"] == {
        "llm_output_parse_error": 1,
        "llm_output_validation_error": 1,
    }


def test_schema_valid_rate_excludes_timeout_and_provider_errors() -> None:
    observer = CountingObserver()
    observer.record(
        _event(
            event_type=LLMReliabilityEventType.ATTEMPT_FAILED,
            error_code="llm_timeout",
        ),
    )
    observer.record(
        _event(
            event_type=LLMReliabilityEventType.RETRY_EXHAUSTED,
            error_code="llm_provider_error",
        ),
    )

    summary = observer.safe_summary()

    assert summary["schema_valid_rate"] is None


def test_logging_observer_redacts_and_includes_event_type(
    caplog: pytest.LogCaptureFixture,
) -> None:
    observer = LoggingObserver()
    event = _event(reason_code=_SECRET)

    with caplog.at_level(logging.INFO, logger="app.llm.reliability"):
        observer.record(event)

    assert _SECRET not in caplog.text
    assert LLMReliabilityEventType.SUCCEEDED.value in caplog.text


def test_null_observer_is_inert() -> None:
    observer = NullObserver()

    observer.record(_event())
