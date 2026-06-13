from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.curriculum.schemas import CurriculumPlan
from app.progress.constants import (
    DEFAULT_USER_ID,
    AdapterSignalType,
    ProgressEventType,
    TopicStatus,
    WeekStatus,
    new_event_id,
    utc_now,
)


class ProgressInitializeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum: CurriculumPlan
    user_id: str = Field(default=DEFAULT_USER_ID, min_length=1, max_length=120)
    goal_id: str | None = Field(default=None, min_length=1, max_length=120)


class ProgressEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=new_event_id)
    curriculum_id: str = Field(min_length=1, max_length=120)
    week_number: int = Field(ge=1, le=52)
    topic_id: str | None = Field(default=None, max_length=120)
    topic_name: str | None = Field(default=None, max_length=180)
    event: ProgressEventType
    value: dict[str, Any] = Field(default_factory=dict)
    logged_at: datetime = Field(default_factory=utc_now)


class TopicProgress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_id: str = Field(min_length=1, max_length=120)
    topic_name: str = Field(min_length=1, max_length=180)
    week_number: int = Field(ge=1, le=52)
    status: TopicStatus = "pending"
    estimated_hours: float = Field(ge=0.0, le=80.0)
    quiz_score: float | None = Field(default=None, ge=0.0, le=1.0)
    updated_at: datetime = Field(default_factory=utc_now)


class WeekProgress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum_id: str = Field(min_length=1, max_length=120)
    week_number: int = Field(ge=1, le=52)
    theme: str = Field(min_length=1, max_length=180)
    status: WeekStatus = "pending"
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    topics: list[TopicProgress] = Field(default_factory=list)
    quiz_score: float | None = Field(default=None, ge=0.0, le=1.0)
    updated_at: datetime = Field(default_factory=utc_now)


class AdapterProgressSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    signal: AdapterSignalType
    severity: str = Field(min_length=1, max_length=40)
    message: str = Field(min_length=1, max_length=500)
    week_number: int | None = Field(default=None, ge=1, le=52)
    topic_id: str | None = Field(default=None, max_length=120)
    value: dict[str, Any] = Field(default_factory=dict)


class ProgressAnalytics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    completion_percentage: float = Field(ge=0.0, le=100.0)
    completed_topic_count: int = Field(ge=0)
    total_topic_count: int = Field(ge=0)
    stuck_topic_count: int = Field(ge=0)
    completed_week_count: int = Field(ge=0)
    total_week_count: int = Field(ge=0)
    average_quiz_score: float | None = Field(default=None, ge=0.0, le=1.0)
    low_quiz_score_count: int = Field(default=0, ge=0)
    signals: list[AdapterProgressSignal] = Field(default_factory=list)


class CurriculumProgressSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum_id: str = Field(min_length=1, max_length=120)
    user_id: str = Field(min_length=1, max_length=120)
    goal_id: str | None = Field(default=None, max_length=120)
    goal: str = Field(min_length=3, max_length=1000)
    current_week_number: int | None = Field(default=None, ge=1, le=52)
    weeks: list[WeekProgress] = Field(default_factory=list)
    events: list[ProgressEvent] = Field(default_factory=list)
    analytics: ProgressAnalytics
    updated_at: datetime = Field(default_factory=utc_now)


class ProgressInitializeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: CurriculumProgressSummary


class ProgressUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum_id: str = Field(min_length=1, max_length=120)
    week_number: int = Field(ge=1, le=52)
    topic_id: str | None = Field(default=None, max_length=120)
    topic_name: str | None = Field(default=None, max_length=180)
    status: TopicStatus | None = None
    event: ProgressEventType | None = None
    value: dict[str, Any] = Field(default_factory=dict)


class ProgressUpdateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: CurriculumProgressSummary
    event: ProgressEvent


class WeekProgressResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    week: WeekProgress


class ProgressExampleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: CurriculumProgressSummary
