from __future__ import annotations

from app.agents.llm.retry_policy_selection import resolve_retry_policy
from app.agents.llm.run_budget_selection import resolve_run_budget
from app.core.settings import Settings
from app.llm.contracts import LLMRetryPolicy
from app.llm.observability.budget import RunBudget


def test_default_settings_resolve_to_current_max_attempts_default() -> None:
    policy = resolve_retry_policy(Settings())

    assert policy.max_attempts == LLMRetryPolicy().max_attempts == 2


def test_max_retries_clamped_to_policy_bound() -> None:
    policy = resolve_retry_policy(Settings(llm_max_retries=5))

    assert policy.max_attempts == 5


def test_backoff_seconds_passed_through() -> None:
    policy = resolve_retry_policy(Settings(llm_retry_backoff_seconds=2.5))

    assert policy.backoff_seconds == 2.5


def test_default_settings_backoff_matches_settings_default() -> None:
    settings = Settings()

    policy = resolve_retry_policy(settings)

    assert policy.backoff_seconds == settings.llm_retry_backoff_seconds == 1.0


def test_bare_llm_retry_policy_default_backoff_is_zero() -> None:
    assert LLMRetryPolicy().backoff_seconds == 0.0


def test_default_settings_resolve_to_current_run_budget_defaults() -> None:
    budget = resolve_run_budget(Settings())

    assert budget.max_llm_calls == RunBudget().max_llm_calls == 16
    assert budget.max_wall_clock_seconds == RunBudget().max_wall_clock_seconds == 120.0


def test_run_budget_max_calls_passed_through() -> None:
    budget = resolve_run_budget(Settings(llm_run_budget_max_calls=5))

    assert budget.max_llm_calls == 5


def test_run_budget_max_wall_clock_seconds_passed_through() -> None:
    budget = resolve_run_budget(Settings(llm_run_budget_max_wall_clock_seconds=30.0))

    assert budget.max_wall_clock_seconds == 30.0
