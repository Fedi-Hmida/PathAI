from __future__ import annotations

from app.agents.deterministic.progress import build_progress_state
from app.agents.mock.base import deterministic_output
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
        goal: LearningGoalDTO,
        curriculum: CurriculumDTO,
        quiz_attempt: QuizAttemptDTO | None = None,
    ) -> ProgressStateDTO:
        return deterministic_output(
            agent_name=self.agent_name,
            output=build_progress_state(goal, curriculum, quiz_attempt),
            fail=self._fail,
            malformed=self._malformed,
        )
