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

    Calibrated 2026-07-20 (Rebuild-40, Big_Audit Step 4) against real measured
    behavior of the allowlisted assessment+knowledge-map+curriculum combo on
    Groq — the first time these defaults were checked against a real provider
    rather than left as an untested guess:

    - The real per-user `/me/workspace/generate` path shares one observer
      across only the knowledge-map and curriculum calls (assessment's own
      10 calls — 5 questions + 5 answer scores — happen earlier, across
      separate `/me/assessment/*` requests, each with its own fresh observer).
      A clean run there used 2 calls and ~5s of wall clock: comfortable
      headroom either way.
    - The orchestration-demo path (`run_straight_line_demo`, and this file's
      own interaction-test construction) shares one observer across all three
      agents in one call: assessment's 10 + knowledge-map's 1 + curriculum's 1
      = exactly 12 calls in a clean run with zero retries — the old default of
      12 left that flow with *no* headroom at all, so a single real retry
      (observed repeatedly as genuine Groq 429s under load in Big_Audit Step 3)
      would degrade an otherwise-healthy run. `max_llm_calls` is raised to 16
      to give that flow real retry headroom while still catching genuine
      runaway/looping behavior.
    - `max_wall_clock_seconds` is left unchanged: every real failure observed
      (Step 3's 429s) failed fast via the existing per-agent `fail_loud` path
      in a few seconds, never by approaching the 120s run-level ceiling, so
      there is no measured case for moving it.

    Production values are settings-driven (`resolve_run_budget`,
    `app/agents/llm/run_budget_selection.py`) — these are the dataclass
    defaults used for direct construction (tests, and any caller that builds
    a `RunBudget` without going through `Settings`), chosen to match the
    settings-driven default exactly when no `PATHAI_LLM_RUN_BUDGET_*` env var
    overrides it.
    """

    max_llm_calls: int = 16
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
