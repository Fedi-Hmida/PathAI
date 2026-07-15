from __future__ import annotations


class AgentError(Exception):
    def __init__(self, agent_name: str, message: str = "agent execution failed") -> None:
        self.agent_name = agent_name
        super().__init__(message)


class ControlledAgentFailure(AgentError):
    pass


class AgentOutputValidationError(AgentError):
    pass


class LLMGenerationUnavailableError(AgentError):
    """An enabled LLM agent could not generate output and no fallback is active.

    Raised (instead of silently degrading to deterministic cross-topic content)
    when `fallback_on_error` is disabled. Carries a stable machine `code` so the
    API/UI can surface an explicit, retry-oriented failure state rather than
    another topic's canned material.
    """

    code = "generation_unavailable"

    def __init__(
        self,
        agent_name: str,
        message: str = "LLM generation is temporarily unavailable.",
    ) -> None:
        super().__init__(agent_name, message)
