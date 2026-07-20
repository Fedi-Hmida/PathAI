from __future__ import annotations

from app.core.settings import Settings
from app.llm.observability.budget import RunBudget


def resolve_run_budget(settings: Settings) -> RunBudget:
    """Build the `RunBudget` a run's shared observer should enforce, from `Settings`.

    Lives under `app/agents/llm/`, not `app/agents/services/activation/`, for
    the same reason `retry_policy_selection.py` and `timeout_policy_selection.py`
    do: it imports from `app.llm.observability`, and only this directory is
    allowlisted to import `app.llm` (Rebuild-12A/12C scope-security boundary).
    """
    return RunBudget(
        max_llm_calls=settings.llm_run_budget_max_calls,
        max_wall_clock_seconds=settings.llm_run_budget_max_wall_clock_seconds,
    )
