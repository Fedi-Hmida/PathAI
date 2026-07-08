from __future__ import annotations

from app.agents.deterministic.adaptation import build_adaptation_output
from app.agents.mock.base import deterministic_output
from app.schemas.adaptation import AdaptationAgentInput, AdaptationAgentOutput


class MockAdapterAgent:
    agent_name = "adapter"

    def __init__(self, *, fail: bool = False, malformed: bool = False) -> None:
        self._fail = fail
        self._malformed = malformed

    def plan_adaptation(self, payload: AdaptationAgentInput) -> AdaptationAgentOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=build_adaptation_output(payload),
            fail=self._fail,
            malformed=self._malformed,
        )
