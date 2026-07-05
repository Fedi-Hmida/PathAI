from __future__ import annotations

from app.agents.mock.base import deterministic_output
from app.fixtures import mock_agents
from app.schemas.adaptation import AdaptationAgentInput, AdaptationAgentOutput


class MockAdapterAgent:
    agent_name = "adapter"

    def __init__(self, *, fail: bool = False, malformed: bool = False) -> None:
        self._fail = fail
        self._malformed = malformed

    def plan_adaptation(self, _payload: AdaptationAgentInput) -> AdaptationAgentOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=mock_agents.ADAPTATION_AGENT_OUTPUT,
            fail=self._fail,
            malformed=self._malformed,
        )
