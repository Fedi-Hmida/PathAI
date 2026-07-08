from __future__ import annotations

from app.llm.observability.observer import LLMReliabilityObserver
from app.llm.observability.sinks import LoggingObserver


def build_default_observer() -> LLMReliabilityObserver:
    """Build the reliability observer a factory-constructed LLM agent should use.

    Lives under `app/agents/llm/`, not `app/agents/services/activation/`, for
    the same reason `client_selection.py` (14C) and `retry_policy_selection.py`
    (15C) do: it imports from `app.llm.observability`, and only this directory
    is allowlisted to import `app.llm` (Rebuild-12A/12C scope-security
    boundary). Agents themselves default their `observer` field to
    `NullObserver` — only this factory-owned path gets a real sink.
    """
    return LoggingObserver()
