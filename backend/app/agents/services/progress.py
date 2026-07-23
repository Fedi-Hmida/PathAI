from __future__ import annotations

from dataclasses import dataclass

from app.agents.contracts import ProgressAgent
from app.agents.mock import MockProgressAgent
from app.agents.services.common import create_or_get, create_or_replace, validate_agent_output
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
        *,
        progress_state_id: str | None = None,
    ) -> ProgressStateDTO:
        output = validate_agent_output(
            agent_name=self.agent.agent_name,
            schema=ProgressStateDTO,
            payload=self.agent.build_progress_state(goal, curriculum, quiz_attempt),
        )
        update: dict[str, object] = {
            "goal_id": goal.goal_id,
            "curriculum_id": curriculum.curriculum_id,
        }
        if progress_state_id is not None:
            update["progress_state_id"] = progress_state_id
        progress_state = output.model_copy(update=update, deep=True)
        # An explicit ID means a per-user workspace regeneration: create it
        # fresh the first time, or overwrite in place on a repeat call -
        # unlike create_or_get's first-write-wins semantics, which fits only
        # the single fixed-ID demo pipeline below.
        if progress_state_id is not None:
            return create_or_replace(
                create=self.progress.create,
                save=self.progress.save,
                record=progress_state,
            )
        return create_or_get(
            create=self.progress.create,
            get=self.progress.get_by_id,
            record=progress_state,
            record_id=progress_state.progress_state_id,
        )


def build_default_progress_agent_service(progress: ProgressService) -> ProgressAgentService:
    """The progress agent has no LLM mode - it is always this deterministic
    default. Exists so `app/orchestration/*_gateway.py` modules never have to
    reference `app.agents.mock` directly - forbidden there by
    `test_agent_scope_security.py`, mirroring
    `app/agents/services/quiz.py`'s `build_default_quiz_agent_service`."""
    return ProgressAgentService(MockProgressAgent(), progress)
