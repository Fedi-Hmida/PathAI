from __future__ import annotations

from app.agents.mock.base import deterministic_output
from app.fixtures import mock_agents
from app.schemas.quiz import QuizAgentInput, QuizAgentOutput, QuizAttemptDTO, QuizScoreOutput


class MockQuizAgent:
    agent_name = "quiz"

    def __init__(self, *, fail: bool = False, malformed: bool = False) -> None:
        self._fail = fail
        self._malformed = malformed

    def build_quiz(self, _payload: QuizAgentInput) -> QuizAgentOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=mock_agents.QUIZ_AGENT_OUTPUT,
            fail=self._fail,
            malformed=self._malformed,
        )

    def score_attempt(self, _attempt: QuizAttemptDTO) -> QuizScoreOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=mock_agents.QUIZ_SCORE_OUTPUT,
            fail=self._fail,
            malformed=self._malformed,
        )
