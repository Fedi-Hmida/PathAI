from __future__ import annotations

from app.core.settings import Settings
from app.llm.contracts import LLMRetryPolicy

_MAX_ATTEMPTS_CEILING = 5


def resolve_retry_policy(settings: Settings) -> LLMRetryPolicy:
    """Build the `LLMRetryPolicy` an LLM-mode agent should use, from `Settings`.

    `Settings.llm_max_retries` counts retries (attempts after the first), so
    `max_attempts = llm_max_retries + 1`. `Settings.llm_max_retries` allows up
    to 5, which would produce `max_attempts=6` — above `LLMRetryPolicy`'s own
    `le=5` bound. Clamped here rather than left to raise `ValidationError` at
    construction time for an operator who set a value within its own declared
    valid range.

    Lives under `app/agents/llm/`, not `app/agents/services/activation/`, for
    the same reason `client_selection.py` does: it imports `LLMRetryPolicy`
    from `app.llm.contracts`, and only this directory is allowlisted to import
    `app.llm` (Rebuild-12A/12C scope-security boundary).
    """
    max_attempts = min(settings.llm_max_retries + 1, _MAX_ATTEMPTS_CEILING)
    return LLMRetryPolicy(
        max_attempts=max_attempts,
        backoff_seconds=settings.llm_retry_backoff_seconds,
        self_correct_on_validation_error=settings.llm_self_correction_enabled,
    )
