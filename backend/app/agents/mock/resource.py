from __future__ import annotations

from app.agents.mock.base import deterministic_output
from app.fixtures import mock_agents
from app.schemas.resource import ResourceAgentInput, ResourceAgentOutput


class MockResourceAgent:
    agent_name = "resource"

    def __init__(self, *, fail: bool = False, malformed: bool = False) -> None:
        self._fail = fail
        self._malformed = malformed

    def attach_resources(self, _payload: ResourceAgentInput) -> ResourceAgentOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=mock_agents.RESOURCE_AGENT_OUTPUT,
            fail=self._fail,
            malformed=self._malformed,
        )
