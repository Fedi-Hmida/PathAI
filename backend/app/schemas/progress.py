from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema, Score, TimestampedDTO, VersionedDTO
from app.schemas.enums import ProgressStatus, TopicProgressStatus
from app.schemas.ids import ConceptId, CurriculumId, GoalId, ProgressId, TopicId


class NextRecommendedAction(BaseSchema):
    topic_id: TopicId | None = None
    label: str = Field(min_length=1, max_length=220)
    reason: str = Field(min_length=1, max_length=500)


class TopicProgressDTO(BaseSchema):
    topic_id: TopicId
    status: TopicProgressStatus
    completion: Score
    last_score: Score | None = None
    attempt_count: int = Field(default=0, ge=0, le=100)
    completed_at: datetime | None = None
    stuck_count: int = Field(default=0, ge=0, le=20)
    notes: str | None = Field(default=None, max_length=800)


class StuckEventDTO(BaseSchema):
    topic_id: TopicId
    concept_ids: list[ConceptId] = Field(default_factory=list, max_length=12)
    reason: str = Field(min_length=1, max_length=500)
    created_at: datetime


class ProgressStateCreate(BaseSchema):
    goal_id: GoalId
    curriculum_id: CurriculumId
    topic_progress: list[TopicProgressDTO] = Field(min_length=1)
    current_topic_id: TopicId | None = None


class ProgressStateDTO(TimestampedDTO, VersionedDTO):
    progress_state_id: ProgressId
    goal_id: GoalId
    curriculum_id: CurriculumId
    status: ProgressStatus
    overall_completion: Score
    current_topic_id: TopicId | None = None
    topic_progress: list[TopicProgressDTO] = Field(min_length=1)
    weak_concepts: list[ConceptId] = Field(default_factory=list, max_length=20)
    stuck_events: list[StuckEventDTO] = Field(default_factory=list, max_length=50)
    last_activity_at: datetime | None = None
    next_recommended_action: NextRecommendedAction | None = None
