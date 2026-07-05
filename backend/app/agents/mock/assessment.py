from __future__ import annotations

from app.agents.mock.base import deterministic_output
from app.fixtures import mock_agents
from app.schemas.assessment import (
    AssessmentAgentInput,
    AssessmentAgentOutput,
    AssessmentAnswerDTO,
    AssessmentScoreOutput,
)


class MockAssessorAgent:
    agent_name = "assessment"

    def __init__(self, *, fail: bool = False, malformed: bool = False) -> None:
        self._fail = fail
        self._malformed = malformed

    def generate_question(self, _payload: AssessmentAgentInput) -> AssessmentAgentOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=mock_agents.ASSESSMENT_AGENT_OUTPUT,
            fail=self._fail,
            malformed=self._malformed,
        )

    def score_answer(self, _answer: AssessmentAnswerDTO) -> AssessmentScoreOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=mock_agents.ASSESSMENT_SCORE_OUTPUT,
            fail=self._fail,
            malformed=self._malformed,
        )
