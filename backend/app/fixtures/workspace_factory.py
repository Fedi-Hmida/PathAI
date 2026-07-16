"""Instantiate a fresh, per-user, per-goal workspace root.

A workspace starts as just the caller's own goal plus an honest, freshly
created orchestration run - nothing else. Knowledge map, curriculum, quiz,
critic review, evaluation, progress, adaptation, and resource attachments are
never cloned from the canonical demo (`canonical_demo.py`): that graph is
shared, fixed reference data for the no-auth demo path only, and a real
per-user workspace must never present its content as the caller's own
(provenance audit finding B5). Each tile starts genuinely absent and is only
populated once the corresponding real work actually happens -
`WorkspaceGenerationService` mints a real knowledge map + curriculum from the
caller's own completed live assessment; the remaining tiles are future work
(Step 2).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.enums import DifficultyLevel, GoalStatus, OrchestrationRunStatus
from app.schemas.goal import LearnerProfile, LearningGoalDTO
from app.schemas.ids import UserId
from app.schemas.orchestration import OrchestrationRunDTO


@dataclass(slots=True)
class WorkspaceBundle:
    goal: LearningGoalDTO
    run: OrchestrationRunDTO

    @property
    def run_id(self) -> str:
        return self.run.run_id

    @property
    def goal_id(self) -> str:
        return self.goal.goal_id


def build_user_workspace(
    owner_user_id: UserId,
    *,
    goal_text: str,
    learner_profile: LearnerProfile | None = None,
) -> WorkspaceBundle:
    """Return a fresh, owner-stamped workspace root: the caller's own goal and
    an honest, not-yet-started orchestration run. No downstream artifact
    (knowledge map, curriculum, quiz, critic review, evaluation, progress,
    adaptation, resources) is seeded - each stays genuinely absent until the
    real pipeline that produces it actually runs."""
    now = datetime.now(UTC)
    goal_id = _new_id("goal")
    run_id = _new_id("run")

    goal = LearningGoalDTO(
        goal_id=goal_id,
        run_id=run_id,
        owner_user_id=owner_user_id,
        goal_text=goal_text,
        normalized_goal_text=" ".join(goal_text.split()),
        status=GoalStatus.CREATED,
        # Never default to a RAG-specific profile - see _neutral_learner_profile.
        learner_profile=learner_profile or _neutral_learner_profile(goal_text),
        demo_seed_id=None,
        created_at=now,
        updated_at=now,
    )
    run = OrchestrationRunDTO(
        run_id=run_id,
        goal_id=goal_id,
        owner_user_id=owner_user_id,
        workflow_version="workspace-v1",
        status=OrchestrationRunStatus.CREATED,
        current_node=None,
        completed_nodes=[],
        failed_nodes=[],
        node_events=[],
        artifact_ids={},
        started_at=now,
        completed_at=None,
        created_at=now,
        updated_at=now,
    )
    return WorkspaceBundle(goal=goal, run=run)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _neutral_learner_profile(goal_text: str) -> LearnerProfile:
    """A topic-neutral default for callers who don't supply their own profile.

    Deliberately empty ``strengths``/``weak_areas`` - the demo's own values
    (``vector_search``, ``chunking``, ``retrieval_evaluation``, ...) would
    otherwise leak RAG-specific vocabulary into every workspace's diagnostic
    concept selection (``diagnostic_focus_for_goal`` matches "retrieval" as a
    substring of "retrieval_evaluation"), regardless of the actual goal.
    """
    return LearnerProfile(
        learner_type="learner",
        strengths=[],
        weak_areas=[],
        time_availability_hours_per_week=5,
        desired_outcome=f"Make real progress on: {goal_text}"[:300],
        preferred_resource_types=[],
        difficulty_target=DifficultyLevel.INTERMEDIATE,
    )
