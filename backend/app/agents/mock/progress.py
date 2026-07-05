from __future__ import annotations

from app.agents.mock.base import deterministic_output
from app.fixtures import canonical_demo as demo
from app.schemas.curriculum import CurriculumDTO
from app.schemas.goal import LearningGoalDTO
from app.schemas.progress import ProgressStateDTO
from app.schemas.quiz import QuizAttemptDTO


class MockProgressAgent:
    agent_name = "progress"

    def __init__(self, *, fail: bool = False, malformed: bool = False) -> None:
        self._fail = fail
        self._malformed = malformed

    def build_progress_state(
        self,
        _goal: LearningGoalDTO,
        _curriculum: CurriculumDTO,
        _quiz_attempt: QuizAttemptDTO | None = None,
    ) -> ProgressStateDTO:
        return deterministic_output(
            agent_name=self.agent_name,
            output=demo.PROGRESS_STATE,
            fail=self._fail,
            malformed=self._malformed,
        )
