from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.critic.constants import (
    DEFAULT_MAX_REVISIONS,
    DEFAULT_REQUIRED_RESOURCES_PER_TOPIC,
    CriticDecisionStatus,
    CriticReviewSource,
    IssueCategory,
    IssueSeverity,
    new_review_id,
    utc_now,
)
from app.curriculum.schemas import CurriculumPlan
from app.rag.schemas import CurriculumResourceAttachmentResponse, ResourceRetrievalResult


class CurriculumIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=700)
    severity: IssueSeverity
    category: IssueCategory
    week_number: int | None = Field(default=None, ge=1, le=52)
    topic_id: str | None = Field(default=None, max_length=120)


class ResourceIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=700)
    severity: IssueSeverity
    category: IssueCategory
    topic_id: str | None = Field(default=None, max_length=120)
    resource_id: str | None = Field(default=None, max_length=120)


class RevisionInstruction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: IssueCategory
    target: str = Field(min_length=1, max_length=180)
    instruction: str = Field(min_length=1, max_length=700)
    severity: IssueSeverity


class PacingReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0.0, le=1.0)
    within_weekly_hours: bool
    total_hours_plausible: bool
    notes: list[str] = Field(default_factory=list)


class PrerequisiteReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0.0, le=1.0)
    ordered_weeks: bool
    weak_missing_topics_addressed: bool
    notes: list[str] = Field(default_factory=list)


class DifficultyReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0.0, le=1.0)
    coherent_progression: bool
    notes: list[str] = Field(default_factory=list)


class ResourceCoverageReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0.0, le=1.0)
    resources_reviewed: bool
    required_resources_per_topic: int = Field(ge=0, le=10)
    average_resources_per_topic: float = Field(ge=0.0)
    notes: list[str] = Field(default_factory=list)


class QualityScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum_score: float = Field(ge=0.0, le=1.0)
    resource_score: float = Field(ge=0.0, le=1.0)
    pacing_score: float = Field(ge=0.0, le=1.0)
    prerequisite_score: float = Field(ge=0.0, le=1.0)
    difficulty_score: float = Field(ge=0.0, le=1.0)
    coverage_score: float = Field(ge=0.0, le=1.0)


class CriticReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum: CurriculumPlan
    resource_attachment: CurriculumResourceAttachmentResponse | None = None
    resource_results: list[ResourceRetrievalResult] = Field(default_factory=list)
    required_resources_per_topic: int = Field(
        default=DEFAULT_REQUIRED_RESOURCES_PER_TOPIC,
        ge=0,
        le=10,
    )
    revision_count: int = Field(default=0, ge=0, le=20)
    max_revisions: int = Field(default=DEFAULT_MAX_REVISIONS, ge=0, le=20)
    use_mock_llm: bool = False


class CriticCurriculumOnlyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum: CurriculumPlan
    revision_count: int = Field(default=0, ge=0, le=20)
    max_revisions: int = Field(default=DEFAULT_MAX_REVISIONS, ge=0, le=20)
    use_mock_llm: bool = False


class CriticReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_id: str = Field(default_factory=new_review_id)
    curriculum_id: str | None = None
    goal: str = Field(min_length=3, max_length=1000)
    timeline_weeks: int = Field(ge=1, le=52)
    hours_per_week: int = Field(ge=1, le=80)
    approved: bool
    decision: CriticDecisionStatus
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    scores: QualityScoreBreakdown
    pacing_review: PacingReview
    prerequisite_review: PrerequisiteReview
    difficulty_review: DifficultyReview
    resource_coverage_review: ResourceCoverageReview
    curriculum_issues: list[CurriculumIssue] = Field(default_factory=list)
    resource_issues: list[ResourceIssue] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    revision_instructions: list[RevisionInstruction] = Field(default_factory=list)
    auto_approved: bool = False
    source: CriticReviewSource = "deterministic"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class CriticRubricSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_threshold: float = Field(ge=0.0, le=1.0)
    required_resources_per_topic: int = Field(ge=0, le=10)
    max_revisions: int = Field(ge=0, le=20)
    curriculum_checks: list[str] = Field(default_factory=list)
    resource_checks: list[str] = Field(default_factory=list)
    decision_rules: list[str] = Field(default_factory=list)


class CriticExampleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review: CriticReviewResult
