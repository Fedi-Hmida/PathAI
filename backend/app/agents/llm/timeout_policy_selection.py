from __future__ import annotations

from app.core.settings import Settings
from app.llm.contracts import LLMTimeoutPolicy


def resolve_timeout_policy(settings: Settings) -> LLMTimeoutPolicy:
    """Build the `LLMTimeoutPolicy` an LLM-mode agent should use, from `Settings`.

    Without this, every LLM agent falls back to `LLMTimeoutPolicy`'s own
    dataclass default (45s) regardless of `Settings.llm_timeout_seconds` -
    and since `OpenAICompatibleLiveLLMClient.generate` takes
    `min(request.timeout.timeout_seconds, self.timeout_seconds)`, that
    default silently wins (and cannot be raised via configuration) whenever
    an operator sets `LLM_TIMEOUT_SECONDS` above 45.

    Lives under `app/agents/llm/`, not `app/agents/services/activation/`, for
    the same reason `retry_policy_selection.py` does: only this directory is
    allowlisted to import `app.llm` (Rebuild-12A/12C scope-security boundary).
    """
    return LLMTimeoutPolicy(timeout_seconds=settings.llm_timeout_seconds)
