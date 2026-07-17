from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from app.agents.services.critic import CriticAgentService
from app.agents.services.curriculum import CurriculumAgentService
from app.agents.services.evaluation import EvaluationAgentService
from app.agents.services.knowledge_map import KnowledgeMapAgentService
from app.schemas.assessment import AssessmentSessionDTO
from app.schemas.critic import CriticReviewDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.enums import AssessmentStatus
from app.schemas.evaluation import EvaluationReportDTO
from app.schemas.goal import LearningGoalDTO
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.services import (
    AssessmentService,
    CriticService,
    CurriculumService,
    EvaluationService,
    KnowledgeMapService,
)


class AssessmentNotCompleteError(Exception):
    """Raised when regeneration is requested before the goal has a completed
    live assessment session."""

    def __init__(self, goal_id: str) -> None:
        self.goal_id = goal_id
        super().__init__(f"no completed assessment session for goal: {goal_id}")


@dataclass(slots=True)
class GeneratedWorkspaceArtifacts:
    knowledge_map: KnowledgeMapDTO
    curriculum: CurriculumDTO
    critic_review: CriticReviewDTO
    evaluation_report: EvaluationReportDTO


@dataclass(slots=True)
class WorkspaceGenerationService:
    """Builds a single user's knowledge map, curriculum, critic review, and
    evaluation report from their own completed live assessment. A fresh
    workspace seeds none of them (`app/fixtures/workspace_factory.py`), so
    the first call here mints fresh IDs and creates them; repeat calls find
    the goal's existing artifacts and regenerate them in place. Quiz,
    resources, progress, and adaptation are deliberately NOT generated here -
    they depend on real user activity (a taken quiz, attached resources) or
    are still backed by a RAG-hardcoded agent (quiz's fixed question bank);
    they stay honestly absent until their own future phase. This is the
    per-user counterpart to the orchestration graph's
    `load_knowledge_map`/`load_curriculum`/`load_critic_review`/
    `load_evaluation` nodes, which only ever run against the fixed canonical
    demo goal (`app/orchestration/runner.py`)."""

    knowledge_map_agent: KnowledgeMapAgentService
    curriculum_agent: CurriculumAgentService
    critic_agent: CriticAgentService
    evaluation_agent: EvaluationAgentService
    assessments: AssessmentService
    knowledge_maps: KnowledgeMapService
    curricula: CurriculumService
    critics: CriticService
    evaluations: EvaluationService

    def generate(self, goal: LearningGoalDTO) -> GeneratedWorkspaceArtifacts:
        session = self._latest_completed_session(goal)
        answers = self.assessments.list_answers_by_session_id(session.assessment_session_id)

        existing_maps = self.knowledge_maps.list_by_goal_id(goal.goal_id)
        existing_curricula = self.curricula.list_by_goal_id(goal.goal_id)
        existing_reviews = self.critics.list_by_goal_id(goal.goal_id)
        existing_evaluations = self.evaluations.list_by_goal_id(goal.goal_id)
        knowledge_map_id = (
            existing_maps[0].knowledge_map_id if existing_maps else _new_id("kmap")
        )
        curriculum_id = (
            existing_curricula[0].curriculum_id if existing_curricula else _new_id("curriculum")
        )
        critic_review_id = (
            existing_reviews[0].critic_review_id if existing_reviews else _new_id("critic")
        )
        evaluation_report_id = (
            existing_evaluations[0].evaluation_report_id
            if existing_evaluations
            else _new_id("eval")
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
        # No resource attachments exist yet (resources are still RAG-corpus-
        # blocked, Rebuild-16) - the critic agent already handles an empty
        # attachment list honestly.
        critic_review = self.critic_agent.review(
            goal,
            knowledge_map,
            curriculum,
            [],
            critic_review_id=critic_review_id,
        )
        # No quiz attempt or adaptation event exists yet (both depend on real
        # user activity this service doesn't fabricate) - the evaluation
        # agent already scores their absence honestly (0.0 on those metrics).
        evaluation_report = self.evaluation_agent.evaluate(
            goal,
            session,
            knowledge_map,
            curriculum,
            [],
            critic_review,
            None,
            None,
            evaluation_report_id=evaluation_report_id,
        )
        return GeneratedWorkspaceArtifacts(
            knowledge_map=knowledge_map,
            curriculum=curriculum,
            critic_review=critic_review,
            evaluation_report=evaluation_report,
        )

    def _latest_completed_session(self, goal: LearningGoalDTO) -> AssessmentSessionDTO:
        sessions = self.assessments.list_sessions_by_goal_id(goal.goal_id)
        completed = [s for s in sessions if s.status == AssessmentStatus.COMPLETED]
        if not completed:
            raise AssessmentNotCompleteError(goal.goal_id)
        return completed[-1]


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"
