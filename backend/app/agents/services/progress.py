from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import ProgressAgent
from app.agents.services.common import create_or_get, validate_agent_output
from app.schemas.curriculum import CurriculumDTO
from app.schemas.goal import LearningGoalDTO
from app.schemas.progress import ProgressStateDTO
from app.schemas.quiz import QuizAttemptDTO
from app.services import ProgressService


@dataclass(slots=True)
class ProgressAgentService:
    agent: ProgressAgent
    progress: ProgressService

    def build(
        self,
        goal: LearningGoalDTO,
        curriculum: CurriculumDTO,
        quiz_attempt: QuizAttemptDTO | None = None,
    ) -> ProgressStateDTO:
        output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=ProgressStateDTO,
            payload=self.agent.build_progress_state(goal, curriculum, quiz_attempt),
        )
        progress_state = output.model_copy(
            update={
                "goal_id": goal.goal_id,
                "curriculum_id": curriculum.curriculum_id,
            },
            deep=True,
        )
        return create_or_get(
            create=self.progress.create,
            get=self.progress.get_by_id,
            record=progress_state,
            record_id=progress_state.progress_state_id,
        )
