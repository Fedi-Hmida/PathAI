from __future__ import annotations

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampedDTO, VersionedDTO
from app.schemas.enums import DifficultyLevel, GoalStatus
from app.schemas.ids import GoalId, RunId, UserId


class LearnerProfile(BaseSchema):
    learner_type: str = Field(min_length=1, max_length=160)
    strengths: list[str] = Field(default_factory=list, max_length=20)
    weak_areas: list[str] = Field(default_factory=list, max_length=20)
    time_availability_hours_per_week: int = Field(ge=1, le=40)
    desired_outcome: str = Field(min_length=1, max_length=300)
    preferred_resource_types: list[str] = Field(default_factory=list, max_length=12)
    difficulty_target: DifficultyLevel = DifficultyLevel.INTERMEDIATE


class LearningGoalCreate(BaseSchema):
    goal_text: str = Field(min_length=5, max_length=500)
    learner_profile: LearnerProfile | None = None
    demo_mode: bool = False
    client_request_id: str | None = Field(default=None, max_length=120)


class LearningGoalDTO(TimestampedDTO, VersionedDTO):
    goal_id: GoalId
    run_id: RunId
    # Owner of this workspace. None = shared/no-auth demo data (unchanged
    # behavior when PATHAI_ENABLE_AUTH is off). Set only for per-user
    # workspaces seeded while auth is enabled.
    owner_user_id: UserId | None = None
    goal_text: str = Field(min_length=5, max_length=500)
    normalized_goal_text: str = Field(min_length=5, max_length=500)
    status: GoalStatus
    learner_profile: LearnerProfile
    constraints: list[str] = Field(default_factory=list, max_length=20)
    target_duration_weeks: int | None = Field(default=None, ge=1, le=52)
    hours_per_week: int | None = Field(default=None, ge=1, le=40)
    demo_seed_id: str | None = Field(default=None, max_length=120)


class LearningGoalSummary(BaseSchema):
    goal_id: GoalId
    text: str = Field(min_length=5, max_length=500)
    status: GoalStatus
