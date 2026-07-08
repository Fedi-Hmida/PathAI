from __future__ import annotations

from app.agents.deterministic.evaluation import build_evaluation_output
from app.agents.mock.base import deterministic_output
from app.schemas.evaluation import EvaluationAgentInput, EvaluationAgentOutput


class MockEvaluationAgent:
    agent_name = "evaluation"

    def __init__(self, *, fail: bool = False, malformed: bool = False) -> None:
        self._fail = fail
        self._malformed = malformed

    def evaluate_run(self, payload: EvaluationAgentInput) -> EvaluationAgentOutput:
        return deterministic_output(
            agent_name=self.agent_name,
            output=build_evaluation_output(payload),
            fail=self._fail,
            malformed=self._malformed,
        )
