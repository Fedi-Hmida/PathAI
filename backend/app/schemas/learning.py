from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.common import (
    AccessType,
    DifficultyLevel,
    GoalStatus,
    ResourceType,
    TopicStatus,
)


class ResourceReferenceSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_id: str | None = None
    title: str = Field(min_length=1, max_length=240)
    url: str = Field(min_length=1, max_length=2000)
    type: ResourceType
    source_name: str | None = Field(default=None, max_length=120)
    difficulty: DifficultyLevel
    estimated_minutes: int = Field(ge=1, le=600)
    quality_score: float = Field(ge=0.0, le=1.0)
    access: AccessType = "free"
    why_recommended: str | None = Field(default=None, max_length=500)


class TopicSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_id: str
    title: str = Field(min_length=1, max_length=180)
    summary: str | None = Field(default=None, max_length=700)
    learning_objectives: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    difficulty: DifficultyLevel
    estimated_hours: float = Field(ge=0.25, le=40.0)
    status: TopicStatus = "pending"
    resources: list[ResourceReferenceSchema] = Field(default_factory=list)


class CurriculumWeekSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    week_number: int = Field(ge=1, le=52)
    title: str = Field(min_length=1, max_length=180)
    goals: list[str] = Field(default_factory=list)
    topics: list[TopicSchema] = Field(default_factory=list)
    estimated_hours: float = Field(ge=1.0, le=80.0)
    deliverable: str | None = Field(default=None, max_length=700)


class CurriculumRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=220)
    overview: str = Field(min_length=1, max_length=1500)
    total_weeks: int = Field(ge=1, le=52)
    weeks: list[CurriculumWeekSchema] = Field(default_factory=list)
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    generated_at: datetime


class KnowledgeMapSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strong: list[str] = Field(default_factory=list)
    weak: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    recommended_level: DifficultyLevel
    confidence_score: float = Field(ge=0.0, le=1.0)


class LearningGoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=180)
    description: str | None = Field(default=None, max_length=1200)
    target_level: DifficultyLevel
    timeline_weeks: int = Field(ge=1, le=52)
    hours_per_week: int = Field(ge=1, le=80)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return " ".join(value.strip().split())


class LearningGoalRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str
    title: str
    description: str | None = None
    target_level: DifficultyLevel
    timeline_weeks: int
    hours_per_week: int
    status: GoalStatus
    knowledge_map: KnowledgeMapSchema | None = None
    curriculum: CurriculumRead | None = None
    created_at: datetime
    updated_at: datetime
