from __future__ import annotations

from app.agents.llm.retry_policy_selection import resolve_retry_policy
from app.core.settings import Settings
from app.llm.contracts import LLMRetryPolicy


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
