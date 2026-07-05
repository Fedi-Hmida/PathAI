from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from app.schemas.base import BaseSchema, TimestampedDTO, VersionedDTO
from app.schemas.enums import CurriculumChangeType, CurriculumStatus, DifficultyLevel
from app.schemas.goal import LearnerProfile
from app.schemas.ids import (
    AttachmentId,
    ConceptId,
    CurriculumId,
    GoalId,
    KnowledgeMapId,
    RunId,
    TopicId,
    WeekId,
)
from app.schemas.knowledge_map import KnowledgeMapDTO


class CurriculumTopicDTO(BaseSchema):
    topic_id: TopicId
    title: str = Field(min_length=1, max_length=220)
    description: str = Field(min_length=1, max_length=800)
    concept_ids: list[ConceptId] = Field(min_length=1, max_length=12)
    difficulty: DifficultyLevel
    estimated_hours: float = Field(gt=0.0, le=40.0)
    learning_outcomes: list[str] = Field(min_length=1, max_length=8)
    sequence_order: int = Field(ge=1, le=200)
    practice_task: str | None = Field(default=None, max_length=800)
    assessment_checkpoint: str | None = Field(default=None, max_length=400)
    resource_attachment_ids: list[AttachmentId] = Field(default_factory=list, max_length=12)
    adaptation_origin: str | None = Field(default=None, max_length=200)


class CurriculumWeekDTO(BaseSchema):
    week_id: WeekId
    week_number: int = Field(ge=1, le=52)
    theme: str = Field(min_length=1, max_length=220)
    topics: list[CurriculumTopicDTO] = Field(min_length=1, max_length=8)
    estimated_hours: float = Field(gt=0.0, le=80.0)
    learning_outcomes: list[str] = Field(min_length=1, max_length=12)
    milestone: str | None = Field(default=None, max_length=400)
    notes: str | None = Field(default=None, max_length=800)


class CurriculumChangeDTO(BaseSchema):
    change_type: CurriculumChangeType
    target_week: int | None = Field(default=None, ge=1, le=52)
    affected_topic_ids: list[TopicId] = Field(default_factory=list, max_length=12)
    affected_concept_ids: list[ConceptId] = Field(default_factory=list, max_length=12)
    reason: str = Field(min_length=1, max_length=800)
    topic_title: str | None = Field(default=None, max_length=220)


class CurriculumCreate(BaseSchema):
    goal_id: GoalId
    knowledge_map_id: KnowledgeMapId
    run_id: RunId
    title: str = Field(min_length=1, max_length=220)
    duration_weeks: int = Field(ge=1, le=52)
    weeks: list[CurriculumWeekDTO] = Field(min_length=1, max_length=52)
    target_outcomes: list[str] = Field(min_length=1, max_length=20)
    assumptions: list[str] = Field(default_factory=list, max_length=20)


class CurriculumDTO(TimestampedDTO, VersionedDTO):
    curriculum_id: CurriculumId
    goal_id: GoalId
    knowledge_map_id: KnowledgeMapId
    run_id: RunId
    status: CurriculumStatus
    title: str = Field(min_length=1, max_length=220)
    duration_weeks: int = Field(ge=1, le=52)
    weeks: list[CurriculumWeekDTO] = Field(min_length=1, max_length=52)
    target_outcomes: list[str] = Field(min_length=1, max_length=20)
    assumptions: list[str] = Field(default_factory=list, max_length=20)
    critic_revision_attempt: int = Field(default=0, ge=0, le=10)
    version: int = Field(default=1, ge=1)
    parent_curriculum_id: CurriculumId | None = None
    revision_reason: str | None = Field(default=None, max_length=400)
    critic_review_ids: list[str] = Field(default_factory=list, max_length=10)
    adaptation_event_ids: list[str] = Field(default_factory=list, max_length=10)
    warnings: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def duration_matches_weeks(self) -> Self:
        if self.duration_weeks != len(self.weeks):
            msg = "duration_weeks must match the number of weeks"
            raise ValueError(msg)
        return self


class CurriculumAgentInput(BaseSchema):
    goal_text: str = Field(min_length=5, max_length=500)
    learner_profile: LearnerProfile
    knowledge_map: KnowledgeMapDTO
    duration_weeks: int = Field(ge=1, le=52)
    hours_per_week: int = Field(ge=1, le=40)
    critic_recommendations: list[str] = Field(default_factory=list, max_length=10)


class CurriculumAgentOutput(BaseSchema):
    title: str = Field(min_length=1, max_length=220)
    duration_weeks: int = Field(ge=1, le=52)
    weeks: list[CurriculumWeekDTO] = Field(min_length=1, max_length=52)
    assumptions: list[str] = Field(default_factory=list, max_length=20)
    target_outcomes: list[str] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def duration_matches_weeks(self) -> Self:
        if self.duration_weeks != len(self.weeks):
            msg = "duration_weeks must match the number of weeks"
            raise ValueError(msg)
        return self
