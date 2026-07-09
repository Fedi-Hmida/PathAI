from __future__ import annotations

from app.llm.observability.budget import RunBudget, RunScopedBudgetObserver
from app.llm.observability.observer import LLMReliabilityObserver
from app.llm.observability.sinks import LoggingObserver


def build_run_scoped_observer(budget: RunBudget | None = None) -> LLMReliabilityObserver:
    """Build one observer shared by every agent constructed in a single run.

    Lives under `app/agents/llm/`, not `app/agents/services/activation/`, for
    the same reason `client_selection.py` (14C) and `retry_policy_selection.py`
    (15C) do: it imports from `app.llm.observability`, and only this directory
    is allowlisted to import `app.llm` (Rebuild-12A/12C scope-security
    boundary).

    Wraps `LoggingObserver` as the inner sink, so existing log output is
    unchanged — every agent built from the same `build_injected_agents` call
    now additionally reports into one shared, run-scoped call-count/wall-clock
    ceiling (Rebuild-22B). Agents themselves still default their `observer`
    field to `NullObserver` when constructed directly (e.g. in tests) —
    only this factory-owned path gets a real, budget-aware sink.
    """
    return RunScopedBudgetObserver(budget or RunBudget(), inner=LoggingObserver())
