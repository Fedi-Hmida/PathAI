from __future__ import annotations

from typing import Protocol

from app.llm.observability.events import LLMReliabilityEvent


class LLMReliabilityObserver(Protocol):
    def record(self, event: LLMReliabilityEvent) -> None: ...


class NullObserver:
    """Default observer: records nothing. Instrumentation is a no-op unless
    a real sink is explicitly injected by the service/composition layer.
    """

    def record(self, event: LLMReliabilityEvent) -> None:
        pass
