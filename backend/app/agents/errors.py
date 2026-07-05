from __future__ import annotations


class AgentError(Exception):
    def __init__(self, agent_name: str, message: str = "agent execution failed") -> None:
        self.agent_name = agent_name
        super().__init__(message)


class ControlledAgentFailure(AgentError):
    pass


class AgentOutputValidationError(AgentError):
    pass
