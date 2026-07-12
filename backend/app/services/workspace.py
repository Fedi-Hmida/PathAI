from __future__ import annotations

from dataclasses import dataclass

from app.fixtures import canonical_demo as demo
from app.fixtures.workspace_factory import WorkspaceBundle, build_user_workspace
from app.repositories.errors import DuplicateRecordError
from app.repositories.protocols import (
    AdaptationRepository,
    CriticReviewRepository,
    CurriculumRepository,
    EvaluationRepository,
    GoalRepository,
    KnowledgeMapRepository,
    OrchestrationRunRepository,
    ProgressRepository,
    QuizRepository,
    ResourceRepository,
)
from app.schemas.auth import UserDTO
from app.schemas.goal import LearnerProfile, LearningGoalDTO
from app.schemas.ids import RunId


class WorkspaceExistsError(Exception):
    """Raised when seeding a workspace for a user who already has one."""


@dataclass(slots=True)
class WorkspaceService:
    """Creates, resolves, and resets a caller's private, owned copy of the
    canonical demo workspace. Only reachable while auth is enabled."""

    goals: GoalRepository
    orchestration_runs: OrchestrationRunRepository
    knowledge_maps: KnowledgeMapRepository
    curricula: CurriculumRepository
    resources: ResourceRepository
    progress_states: ProgressRepository
    quizzes: QuizRepository
    adaptations: AdaptationRepository
    critics: CriticReviewRepository
    evaluations: EvaluationRepository

    def get_run_id(self, user: UserDTO) -> RunId | None:
        goal = self.goals.find_by_owner(user.user_id)
        return goal.run_id if goal is not None else None

    def get_owned_goal(self, user: UserDTO) -> LearningGoalDTO | None:
        return self.goals.find_by_owner(user.user_id)

    def seed(
        self,
        user: UserDTO,
        goal_text: str,
        learner_profile: LearnerProfile | None = None,
    ) -> RunId:
        if self.goals.find_by_owner(user.user_id) is not None:
            raise WorkspaceExistsError
        bundle = build_user_workspace(
            user.user_id,
            goal_text=goal_text,
            learner_profile=learner_profile,
        )
        self._persist(bundle)
        return bundle.run_id

    def reset(
        self,
        user: UserDTO,
        goal_text: str,
        learner_profile: LearnerProfile | None = None,
    ) -> RunId:
        existing = self.goals.find_by_owner(user.user_id)
        if existing is not None:
            # Detach the two ownership roots. Every artifact authorizes through
            # its goal, so removing the goal makes the old graph unreachable.
            # (Cascade-deleting the orphaned artifacts is a documented follow-up.)
            self.orchestration_runs.delete(existing.run_id)
            self.goals.delete(existing.goal_id)
        bundle = build_user_workspace(
            user.user_id,
            goal_text=goal_text,
            learner_profile=learner_profile,
        )
        self._persist(bundle)
        return bundle.run_id

    def _persist(self, bundle: WorkspaceBundle) -> None:
        self._ensure_corpus()
        self.goals.create(bundle.goal)
        self.orchestration_runs.create(bundle.run)
        self.knowledge_maps.create(bundle.knowledge_map)
        self.curricula.create(bundle.curriculum)
        for attachment in bundle.resource_attachments:
            self.resources.create_attachment(attachment)
        self.progress_states.create(bundle.progress_state)
        self.quizzes.create_quiz(bundle.quiz)
        self.quizzes.create_attempt(bundle.quiz_attempt)
        self.adaptations.create(bundle.adaptation_event)
        self.critics.create(bundle.critic_review)
        self.evaluations.create(bundle.evaluation_report)

    def _ensure_corpus(self) -> None:
        # The curated resource corpus is shared, global reference data. Seed it
        # once; subsequent workspaces reuse it.
        for resource in demo.RESOURCE_CORPUS:
            try:
                self.resources.create_resource(resource)
            except DuplicateRecordError:
                pass
