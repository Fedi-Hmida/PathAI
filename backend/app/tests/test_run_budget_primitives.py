from __future__ import annotations

import pytest

from app.llm.observability import (
    CountingObserver,
    LLMReliabilityEvent,
    LLMReliabilityEventType,
    RunBudget,
    RunScopedBudgetObserver,
)
from app.llm.observability.budget import MAX_LLM_CALLS_REASON, MAX_WALL_CLOCK_REASON

_SECRET = "Bearer sk-fake-secret-token-1234567890"


def _event(**overrides: object) -> LLMReliabilityEvent:
    fields: dict[str, object] = {
        "event_type": LLMReliabilityEventType.ATTEMPT_STARTED,
        "schema_name": "KnowledgeMapAgentOutput",
        "attempt": 1,
        "max_attempts": 2,
    }
    fields.update(overrides)
    return LLMReliabilityEvent(**fields)


class _FakeClock:
    """A clock that only moves when a test moves it. No sleeping, ever."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class _SpyObserver:
    def __init__(self) -> None:
        self.events: list[LLMReliabilityEvent] = []

    def record(self, event: LLMReliabilityEvent) -> None:
        self.events.append(event)


def test_run_budget_defaults() -> None:
    budget = RunBudget()

    assert budget.max_llm_calls == 16
    assert budget.max_wall_clock_seconds == 120.0


@pytest.mark.parametrize("max_llm_calls", [0, -1])
def test_non_positive_max_llm_calls_is_rejected(max_llm_calls: int) -> None:
    with pytest.raises(ValueError, match="max_llm_calls"):
        RunBudget(max_llm_calls=max_llm_calls)


@pytest.mark.parametrize("max_wall_clock_seconds", [0.0, -1.5])
def test_non_positive_max_wall_clock_is_rejected(max_wall_clock_seconds: float) -> None:
    with pytest.raises(ValueError, match="max_wall_clock_seconds"):
        RunBudget(max_wall_clock_seconds=max_wall_clock_seconds)


def test_only_attempt_started_increments_the_call_count() -> None:
    observer = RunScopedBudgetObserver(RunBudget(max_llm_calls=5))

    observer.record(_event(event_type=LLMReliabilityEventType.SUCCEEDED))
    observer.record(_event(event_type=LLMReliabilityEventType.ATTEMPT_FAILED))
    observer.record(_event(event_type=LLMReliabilityEventType.RETRY_EXHAUSTED))
    observer.record(_event(event_type=LLMReliabilityEventType.FALLBACK_USED))

    assert observer.safe_summary()["llm_call_count"] == 0
    assert observer.exhausted() is False

    observer.record(_event(event_type=LLMReliabilityEventType.ATTEMPT_STARTED))

    assert observer.safe_summary()["llm_call_count"] == 1


def test_call_count_exhausts_at_the_limit_not_before() -> None:
    observer = RunScopedBudgetObserver(RunBudget(max_llm_calls=2))

    observer.record(_event())
    assert observer.exhausted() is False

    observer.record(_event())
    assert observer.exhausted() is True
    assert observer.safe_summary()["exhaustion_reason"] == MAX_LLM_CALLS_REASON


def test_wall_clock_exhaustion_uses_the_injected_clock() -> None:
    clock = _FakeClock()
    observer = RunScopedBudgetObserver(
        RunBudget(max_llm_calls=100, max_wall_clock_seconds=10.0),
        clock=clock,
    )

    observer.record(_event())
    assert observer.exhausted() is False

    clock.now = 10.0

    assert observer.exhausted() is True
    assert observer.safe_summary()["exhaustion_reason"] == MAX_WALL_CLOCK_REASON


def test_wall_clock_starts_on_first_event_not_on_construction() -> None:
    clock = _FakeClock()
    observer = RunScopedBudgetObserver(
        RunBudget(max_llm_calls=100, max_wall_clock_seconds=10.0),
        clock=clock,
    )

    # A long gap between construction and the run starting must not count.
    clock.now = 1_000.0
    observer.record(_event())

    assert observer.exhausted() is False
    assert observer.safe_summary()["elapsed_seconds"] == 0.0


def test_every_event_is_delegated_to_the_inner_observer() -> None:
    inner = CountingObserver()
    observer = RunScopedBudgetObserver(RunBudget(max_llm_calls=100), inner=inner)

    observer.record(_event(event_type=LLMReliabilityEventType.ATTEMPT_STARTED))
    observer.record(_event(event_type=LLMReliabilityEventType.SUCCEEDED))

    assert inner.safe_summary()["counts_by_event_type"] == {
        "attempt_started": 1,
        "succeeded": 1,
    }


def test_default_inner_observer_is_inert() -> None:
    observer = RunScopedBudgetObserver(RunBudget(max_llm_calls=1))

    observer.record(_event())

    assert observer.exhausted() is True


def test_exhausted_is_idempotent_and_emits_no_events() -> None:
    inner = _SpyObserver()
    observer = RunScopedBudgetObserver(RunBudget(max_llm_calls=1), inner=inner)

    observer.record(_event())
    event_count_after_record = len(inner.events)

    for _ in range(5):
        assert observer.exhausted() is True

    assert len(inner.events) == event_count_after_record


def test_exactly_one_run_budget_exhausted_event_is_emitted() -> None:
    inner = _SpyObserver()
    observer = RunScopedBudgetObserver(RunBudget(max_llm_calls=1), inner=inner)

    for _ in range(4):
        observer.record(_event())

    exhaustion_events = [
        event
        for event in inner.events
        if event.event_type == LLMReliabilityEventType.RUN_BUDGET_EXHAUSTED
    ]
    assert len(exhaustion_events) == 1
    assert exhaustion_events[0].reason_code == MAX_LLM_CALLS_REASON
    assert exhaustion_events[0].schema_name == "KnowledgeMapAgentOutput"


def test_exhaustion_event_carries_no_dynamic_content() -> None:
    inner = _SpyObserver()
    observer = RunScopedBudgetObserver(RunBudget(max_llm_calls=1), inner=inner)

    observer.record(_event(provider=_SECRET, reason_code=_SECRET))

    exhaustion_event = next(
        event
        for event in inner.events
        if event.event_type == LLMReliabilityEventType.RUN_BUDGET_EXHAUSTED
    )
    assert exhaustion_event.reason_code == MAX_LLM_CALLS_REASON
    assert _SECRET not in exhaustion_event.model_dump_json()


def test_safe_summary_leaks_no_secret_shaped_value() -> None:
    observer = RunScopedBudgetObserver(RunBudget(max_llm_calls=1))

    observer.record(_event(provider=_SECRET, reason_code=_SECRET))

    assert _SECRET not in repr(observer.safe_summary())


def test_safe_summary_reports_budget_limits_and_progress() -> None:
    clock = _FakeClock()
    observer = RunScopedBudgetObserver(
        RunBudget(max_llm_calls=4, max_wall_clock_seconds=30.0),
        clock=clock,
    )

    observer.record(_event())
    clock.now = 7.5

    assert observer.safe_summary() == {
        "llm_call_count": 1,
        "max_llm_calls": 4,
        "elapsed_seconds": 7.5,
        "max_wall_clock_seconds": 30.0,
        "exhausted": False,
        "exhaustion_reason": None,
    }
