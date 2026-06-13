from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

DifficultyLevel = Literal["beginner", "intermediate", "advanced"]
ResourceType = Literal["article", "video", "course", "documentation", "book", "paper", "exercise"]
AccessType = Literal["free", "institutional", "paid", "unknown"]
TopicStatus = Literal["pending", "in_progress", "done", "stuck"]
GoalStatus = Literal[
    "draft",
    "assessing",
    "ready_for_generation",
    "generating",
    "active",
    "paused",
    "completed",
]


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_uuid() -> str:
    return str(uuid4())


class ResourceReference(BaseModel):
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


class Topic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_id: str = Field(default_factory=new_uuid)
    title: str = Field(min_length=1, max_length=180)
    summary: str | None = Field(default=None, max_length=700)
    learning_objectives: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    difficulty: DifficultyLevel
    estimated_hours: float = Field(ge=0.25, le=40.0)
    status: TopicStatus = "pending"
    resources: list[ResourceReference] = Field(default_factory=list)


class CurriculumWeek(BaseModel):
    model_config = ConfigDict(extra="forbid")

    week_number: int = Field(ge=1, le=52)
    title: str = Field(min_length=1, max_length=180)
    goals: list[str] = Field(default_factory=list)
    topics: list[Topic] = Field(default_factory=list)
    estimated_hours: float = Field(ge=1.0, le=80.0)
    deliverable: str | None = Field(default=None, max_length=700)


class Curriculum(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(default=1, ge=1)
    title: str = Field(min_length=1, max_length=220)
    overview: str = Field(min_length=1, max_length=1500)
    total_weeks: int = Field(ge=1, le=52)
    weeks: list[CurriculumWeek] = Field(default_factory=list)
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    generated_at: datetime = Field(default_factory=utc_now)


class KnowledgeMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strong: list[str] = Field(default_factory=list)
    weak: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    recommended_level: DifficultyLevel
    confidence_score: float = Field(ge=0.0, le=1.0)


class CurriculumHistorySnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: int = Field(ge=1)
    changed_at: datetime = Field(default_factory=utc_now)
    reason: str = Field(min_length=1, max_length=500)
    weeks_affected: list[int] = Field(default_factory=list)
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    curriculum: Curriculum | None = None


class LearningGoal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str = Field(default_factory=new_uuid)
    title: str = Field(min_length=3, max_length=180)
    description: str | None = Field(default=None, max_length=1200)
    target_level: DifficultyLevel
    timeline_weeks: int = Field(ge=1, le=52)
    hours_per_week: int = Field(ge=1, le=80)
    status: GoalStatus = "draft"
    knowledge_map: KnowledgeMap | None = None
    curriculum: Curriculum | None = None
    curriculum_history: list[CurriculumHistorySnapshot] = Field(
        default_factory=list,
        max_length=5,
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
