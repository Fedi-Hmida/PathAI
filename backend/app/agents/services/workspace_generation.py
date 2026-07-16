from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.agents.services.curriculum import CurriculumAgentService
from app.agents.services.knowledge_map import KnowledgeMapAgentService
from app.schemas.assessment import AssessmentSessionDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.enums import AssessmentStatus
from app.schemas.goal import LearningGoalDTO
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.services import AssessmentService, CurriculumService, KnowledgeMapService


class AssessmentNotCompleteError(Exception):
    """Raised when regeneration is requested before the goal has a completed
    live assessment session."""

    def __init__(self, goal_id: str) -> None:
        self.goal_id = goal_id
        super().__init__(f"no completed assessment session for goal: {goal_id}")


@dataclass(slots=True)
class WorkspaceGenerationService:
    """Builds a single user's knowledge map and curriculum from their own
    completed live assessment. A fresh workspace seeds neither
    (`app/fixtures/workspace_factory.py`), so the first call here mints new
    IDs and creates them; repeat calls find the goal's existing pair and
    regenerate it in place. This is the per-user counterpart to the
    orchestration graph's `load_knowledge_map`/`load_curriculum` nodes, which
    only ever run against the fixed canonical demo goal
    (`app/orchestration/runner.py`)."""

    knowledge_map_agent: KnowledgeMapAgentService
    curriculum_agent: CurriculumAgentService
    assessments: AssessmentService
    knowledge_maps: KnowledgeMapService
    curricula: CurriculumService

    def generate(self, goal: LearningGoalDTO) -> tuple[KnowledgeMapDTO, CurriculumDTO]:
        session = self._latest_completed_session(goal)
        answers = self.assessments.list_answers_by_session_id(session.assessment_session_id)

        existing_maps = self.knowledge_maps.list_by_goal_id(goal.goal_id)
        existing_curricula = self.curricula.list_by_goal_id(goal.goal_id)
        knowledge_map_id = (
            existing_maps[0].knowledge_map_id if existing_maps else _new_id("kmap")
        )
        curriculum_id = (
            existing_curricula[0].curriculum_id if existing_curricula else _new_id("curriculum")
        )

        knowledge_map = self.knowledge_map_agent.build(
            goal,
            session,
            answers,
            knowledge_map_id=knowledge_map_id,
        )
        curriculum = self.curriculum_agent.build(
            goal,
            knowledge_map,
            curriculum_id=curriculum_id,
        )
        return knowledge_map, curriculum

    def _latest_completed_session(self, goal: LearningGoalDTO) -> AssessmentSessionDTO:
        sessions = self.assessments.list_sessions_by_goal_id(goal.goal_id)
        completed = [s for s in sessions if s.status == AssessmentStatus.COMPLETED]
        if not completed:
            raise AssessmentNotCompleteError(goal.goal_id)
        return completed[-1]


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"
