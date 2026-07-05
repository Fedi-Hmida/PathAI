from __future__ import annotations


class OrchestrationError(Exception):
    """Base error for orchestration boundary failures."""


class OrchestrationNodeError(OrchestrationError):
    """Raised when a graph node fails in a controlled way."""
