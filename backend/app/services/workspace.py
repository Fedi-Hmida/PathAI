from __future__ import annotations

from dataclasses import dataclass

from app.fixtures import canonical_demo as demo
from app.fixtures.workspace_factory import WorkspaceBundle, build_user_workspace
from app.repositories.errors import DuplicateRecordError
from app.repositories.protocols import (
    GoalRepository,
    OrchestrationRunRepository,
    ResourceRepository,
)
from app.schemas.auth import UserDTO
from app.schemas.goal import LearnerProfile, LearningGoalDTO
from app.schemas.ids import RunId


class WorkspaceExistsError(Exception):
    """Raised when seeding a workspace for a user who already has one."""


@dataclass(slots=True)
class WorkspaceService:
    """Creates, resolves, and resets a caller's private, owned workspace root
    (goal + orchestration run). Only reachable while auth is enabled. Holds no
    reference to downstream artifact repositories - a fresh workspace seeds
    none of them (provenance audit finding B5); they're populated later by
    the real generation/agent pipelines that own them."""

    goals: GoalRepository
    orchestration_runs: OrchestrationRunRepository
    resources: ResourceRepository

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
            # its goal, so removing the goal makes any real artifacts the
            # caller had already generated (knowledge map, curriculum, ...)
            # unreachable. (Cascade-deleting those orphans is a documented
            # follow-up.)
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

    def _ensure_corpus(self) -> None:
        # The curated resource corpus is shared, global reference data. Seed it
        # once; subsequent workspaces reuse it.
        for resource in demo.RESOURCE_CORPUS:
            try:
                self.resources.create_resource(resource)
            except DuplicateRecordError:
                pass
