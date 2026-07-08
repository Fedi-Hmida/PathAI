from __future__ import annotations

from app.core.settings import Settings
from app.llm.contracts import LLMClient
from app.llm.fake_client import FakeLLMClient
from app.llm.live_client import build_live_client_from_settings


class UnselectableLLMProviderError(ValueError):
    """Raised when no LLM client can be selected for the given settings.

    Deliberately does not import anything from `app.agents.services.activation`
    — that package's `__init__.py` imports this module (via the agent
    construction factory), so a reverse import here would create a circular
    import at package-init time. This module only depends on `app.core` and
    `app.llm`, never on the service/switch layer above it.
    """


def build_llm_client_for_agent(settings: Settings) -> LLMClient:
    """Build the LLM client an `LLM` switch should use, per `settings.llm_provider`.

    - `"mock"` never reaches this function in the real activation flow (a
      `DETERMINISTIC` switch never calls it) — if it is called anyway, that is
      a misconfiguration, and it fails loudly rather than silently returning
      a client that shouldn't exist.
    - `"fake"` returns the deterministic, in-process, no-network `FakeLLMClient`
      — safe to use to prove the activation wiring works without credentials.
    - anything else delegates to the existing live-client boundary, which
      already fails closed (`LiveLLMNotConfiguredError`) on incomplete
      provider configuration.

    Lives under `app/agents/llm/`, not `app/agents/services/activation/`,
    because the scope-security boundary established in Rebuild-12A/12C
    (`test_llm_agent_scope_security.py`, `test_llm_scope_security.py`) only
    allowlists this directory for importing `app.llm`. Keeping the client
    selection here preserves that boundary unchanged instead of widening it.
    """
    provider = settings.llm_provider.strip().lower()

    if provider == "mock":
        msg = (
            "build_llm_client_for_agent must not be called while llm_provider "
            "is 'mock' — an LLM-mode switch requires 'fake' or a real provider."
        )
        raise UnselectableLLMProviderError(msg)

    if provider == "fake":
        return FakeLLMClient()

    return build_live_client_from_settings(settings)
