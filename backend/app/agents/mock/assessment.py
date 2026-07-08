from __future__ import annotations

from app.agents.deterministic.assessment import build_question_output, score_answer
from app.agents.mock.base import deterministic_output
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

    def generate_question(self, payload: AssessmentAgentInput) -> AssessmentAgentOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=build_question_output(payload),
            fail=self._fail,
            malformed=self._malformed,
        )

    def score_answer(self, answer: AssessmentAnswerDTO) -> AssessmentScoreOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=score_answer(answer),
            fail=self._fail,
            malformed=self._malformed,
        )
