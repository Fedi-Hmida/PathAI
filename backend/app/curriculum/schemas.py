from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.assessment.schemas import KnowledgeMap
from app.curriculum.constants import (
    DEFAULT_USER_ID,
    CurriculumSource,
    CurriculumStatus,
    DifficultyLevel,
    TopicPriority,
    ValidationSeverity,
)


class CurriculumGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(default=DEFAULT_USER_ID, min_length=1, max_length=120)
    goal_id: str | None = Field(default=None, min_length=1, max_length=120)
    assessment_session_id: str | None = Field(default=None, min_length=1, max_length=120)
    goal: str | None = Field(default=None, min_length=3, max_length=1000)
    timeline_weeks: int | None = Field(default=None, ge=1, le=52)
    hours_per_week: int | None = Field(default=None, ge=1, le=80)
    knowledge_map: KnowledgeMap | None = None

    @model_validator(mode="after")
    def require_assessment_or_explicit_payload(self) -> "CurriculumGenerationRequest":
        if self.assessment_session_id:
            return self
        missing = [
            name
            for name, value in {
                "goal": self.goal,
                "timeline_weeks": self.timeline_weeks,
                "hours_per_week": self.hours_per_week,
                "knowledge_map": self.knowledge_map,
            }.items()
            if value is None
        ]
        if missing:
            raise ValueError(
                "Either assessment_session_id or explicit goal, timeline_weeks, "
                f"hours_per_week, and knowledge_map are required. Missing: {', '.join(missing)}."
            )
        return self


class CurriculumSubtopic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=180)
    estimated_hours: float = Field(ge=0.25, le=20.0)
    learning_outcome: str = Field(min_length=3, max_length=400)


class CurriculumTopic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=180)
    priority: TopicPriority
    difficulty: DifficultyLevel
    estimated_hours: float = Field(ge=0.25, le=80.0)
    rationale: str = Field(min_length=3, max_length=600)
    subtopics: list[CurriculumSubtopic] = Field(default_factory=list, min_length=1)
    prerequisites: list[str] = Field(default_factory=list, max_length=8)
    learning_outcomes: list[str] = Field(default_factory=list, min_length=1, max_length=8)
    project_or_application: bool = False


class CurriculumMilestone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=3, max_length=700)
    deliverable: str = Field(min_length=3, max_length=400)
    evaluation_hint: str = Field(min_length=3, max_length=400)


class CurriculumWeek(BaseModel):
    model_config = ConfigDict(extra="forbid")

    week_number: int = Field(ge=1, le=52)
    theme: str = Field(min_length=3, max_length=180)
    weekly_goal: str = Field(min_length=3, max_length=500)
    milestone: CurriculumMilestone
    estimated_hours: float = Field(ge=1.0, le=80.0)
    difficulty: DifficultyLevel
    topics: list[CurriculumTopic] = Field(default_factory=list, min_length=1)
    project_or_application: bool = False


class DifficultyProgression(BaseModel):
    model_config = ConfigDict(extra="forbid")

    starting_level: DifficultyLevel
    ending_level: DifficultyLevel
    weekly_levels: list[DifficultyLevel] = Field(default_factory=list, min_length=1)
    rationale: str = Field(min_length=3, max_length=700)


class CurriculumValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=700)
    severity: ValidationSeverity
    week_number: int | None = Field(default=None, ge=1, le=52)


class CurriculumPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum_id: str
    user_id: str = DEFAULT_USER_ID
    goal_id: str | None = None
    assessment_session_id: str | None = None
    goal: str = Field(min_length=3, max_length=1000)
    timeline_weeks: int = Field(ge=1, le=52)
    hours_per_week: int = Field(ge=1, le=80)
    knowledge_map: KnowledgeMap
    weeks: list[CurriculumWeek] = Field(default_factory=list, min_length=1)
    total_hours: float = Field(ge=1.0)
    difficulty_progression: DifficultyProgression
    generation_notes: list[str] = Field(default_factory=list)
    source: CurriculumSource = "deterministic"
    status: CurriculumStatus = "generated"
    validation_issues: list[CurriculumValidationIssue] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CurriculumGenerationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum: CurriculumPlan
    validation_issues: list[CurriculumValidationIssue] = Field(default_factory=list)


class CurriculumValidationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    validation_issues: list[CurriculumValidationIssue] = Field(default_factory=list)
    message: str


class CurriculumResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum: CurriculumPlan


class CurriculumGenerateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: CurriculumGenerationResult


class CurriculumExampleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request: CurriculumGenerationRequest
    result: CurriculumGenerationResult


class CompletedCurriculumStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Annotated[CurriculumStatus, Field(pattern="^generated$")] = "generated"
