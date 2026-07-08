from __future__ import annotations

from app.agents.deterministic.curriculum import build_curriculum_output
from app.agents.mock.base import deterministic_output
from app.fixtures import mock_agents
from app.schemas.curriculum import CurriculumAgentInput, CurriculumAgentOutput


class MockCurriculumAgent:
    agent_name = "curriculum"

    def __init__(self, *, fail: bool = False, malformed: bool = False) -> None:
        self._fail = fail
        self._malformed = malformed

    def build_curriculum(self, payload: CurriculumAgentInput) -> CurriculumAgentOutput:
        if self._fail or self._malformed:
            return deterministic_output(
                agent_name=self.agent_name,
                output=mock_agents.CURRICULUM_AGENT_OUTPUT,
                fail=self._fail,
                malformed=self._malformed,
            )
        return build_curriculum_output(payload)
