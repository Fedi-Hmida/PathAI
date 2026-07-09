from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from app.llm.observability.events import LLMReliabilityEvent, LLMReliabilityEventType
from app.llm.observability.observer import LLMReliabilityObserver, NullObserver

MAX_LLM_CALLS_REASON = "max_llm_calls"
MAX_WALL_CLOCK_REASON = "max_wall_clock_seconds"


@dataclass(frozen=True, slots=True)
class RunBudget:
    """A ceiling on one orchestration run, above any single agent's retry policy.

    Defaults are deliberately non-binding for every path that exists today: the
    most expensive single-agent run is Assessment at 10 LLM calls (5 questions +
    5 answer scores). They have never been measured against a real provider.
    """

    max_llm_calls: int = 12
    max_wall_clock_seconds: float = 120.0

    def __post_init__(self) -> None:
        if self.max_llm_calls <= 0:
            msg = "max_llm_calls must be greater than zero."
            raise ValueError(msg)
        if self.max_wall_clock_seconds <= 0:
            msg = "max_wall_clock_seconds must be greater than zero."
            raise ValueError(msg)


class RunScopedBudgetObserver:
    """Aggregates one run's reliability events and reports budget exhaustion.

    Structurally implements `LLMReliabilityObserver`. It decorates an inner
    observer rather than replacing it: every event is delegated through, so an
    injected `LoggingObserver`/`CountingObserver` keeps behaving exactly as it
    did before this observer existed.

    `ATTEMPT_STARTED` is the meter for LLM calls — `retry.py` emits it once per
    provider call attempt, retries included.

    Reporting only. `exhausted()` never raises and has no side effects; acting
    on it (degrading agents to their deterministic fallback) is the wiring
    phase's job, not this object's.
    """

    def __init__(
        self,
        budget: RunBudget,
        inner: LLMReliabilityObserver | None = None,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._budget = budget
        self._inner = inner or NullObserver()
        self._clock = clock
        self._llm_call_count = 0
        self._started_at: float | None = None
        self._exhaustion_reason: str | None = None

    def record(self, event: LLMReliabilityEvent) -> None:
        self._inner.record(event)

        if self._started_at is None:
            self._started_at = self._clock()
        if event.event_type == LLMReliabilityEventType.ATTEMPT_STARTED:
            self._llm_call_count += 1

        self._emit_exhaustion_once(event.schema_name)

    def exhausted(self) -> bool:
        return self._current_exhaustion_reason() is not None

    def safe_summary(self) -> dict[str, object]:
        # Report the latched reason when one was emitted, otherwise the live
        # one — the wall clock can cross the limit between recorded events.
        reason = self._exhaustion_reason or self._current_exhaustion_reason()
        return {
            "llm_call_count": self._llm_call_count,
            "max_llm_calls": self._budget.max_llm_calls,
            "elapsed_seconds": self._elapsed_seconds(),
            "max_wall_clock_seconds": self._budget.max_wall_clock_seconds,
            "exhausted": reason is not None,
            "exhaustion_reason": reason,
        }

    def _emit_exhaustion_once(self, schema_name: str) -> None:
        if self._exhaustion_reason is not None:
            return
        reason = self._current_exhaustion_reason()
        if reason is None:
            return
        self._exhaustion_reason = reason
        self._inner.record(
            LLMReliabilityEvent(
                event_type=LLMReliabilityEventType.RUN_BUDGET_EXHAUSTED,
                schema_name=schema_name,
                attempt=1,
                max_attempts=1,
                reason_code=reason,
            ),
        )

    def _current_exhaustion_reason(self) -> str | None:
        if self._llm_call_count >= self._budget.max_llm_calls:
            return MAX_LLM_CALLS_REASON
        if self._elapsed_seconds() >= self._budget.max_wall_clock_seconds:
            return MAX_WALL_CLOCK_REASON
        return None

    def _elapsed_seconds(self) -> float:
        if self._started_at is None:
            return 0.0
        return self._clock() - self._started_at
