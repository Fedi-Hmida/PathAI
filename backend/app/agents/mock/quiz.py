from __future__ import annotations

from app.agents.deterministic.quiz import build_quiz_output, score_quiz_attempt
from app.agents.mock.base import deterministic_output
from app.schemas.quiz import (
    QuizAgentInput,
    QuizAgentOutput,
    QuizAttemptDTO,
    QuizQuestionDTO,
    QuizScoreOutput,
)


class MockQuizAgent:
    agent_name = "quiz"

    def __init__(self, *, fail: bool = False, malformed: bool = False) -> None:
        self._fail = fail
        self._malformed = malformed

    def build_quiz(self, payload: QuizAgentInput) -> QuizAgentOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=build_quiz_output(payload),
            fail=self._fail,
            malformed=self._malformed,
        )

    def score_attempt(
        self,
        attempt: QuizAttemptDTO,
        questions: list[QuizQuestionDTO],
    ) -> QuizScoreOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=score_quiz_attempt(attempt, questions),
            fail=self._fail,
            malformed=self._malformed,
        )
