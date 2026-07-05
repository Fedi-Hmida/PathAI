from __future__ import annotations

from app.agents.mock.base import deterministic_output
from app.fixtures import mock_agents
from app.schemas.critic import CriticAgentInput, CriticAgentOutput


class MockCriticAgent:
    agent_name = "critic"

    def __init__(self, *, fail: bool = False, malformed: bool = False) -> None:
        self._fail = fail
        self._malformed = malformed

    def review_curriculum(self, _payload: CriticAgentInput) -> CriticAgentOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=mock_agents.CRITIC_AGENT_OUTPUT,
            fail=self._fail,
            malformed=self._malformed,
        )
