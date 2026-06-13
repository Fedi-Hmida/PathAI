from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.adapter.constants import (
    AdaptationDecisionStatus,
    AdaptationSignalSeverity,
    AdaptationTriggerReason,
    ReplanFlowStep,
    new_adaptation_id,
    utc_now,
)
from app.curriculum.schemas import CurriculumPlan
from app.progress.schemas import CurriculumProgressSummary
from app.quiz.schemas import QuizHistorySummary
from app.rag.schemas import CurriculumResourceAttachmentResponse


class AdaptationSignal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: AdaptationTriggerReason
    severity: AdaptationSignalSeverity
    message: str = Field(min_length=1, max_length=600)
    week_number: int | None = Field(default=None, ge=1, le=52)
    topic_id: str | None = Field(default=None, max_length=120)
    topic_name: str | None = Field(default=None, max_length=180)
    value: dict[str, Any] = Field(default_factory=dict)


class AffectedTopic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    week_number: int = Field(ge=1, le=52)
    topic_id: str = Field(min_length=1, max_length=120)
    topic_name: str = Field(min_length=1, max_length=180)
    reason: AdaptationTriggerReason


class AffectedWeek(BaseModel):
    model_config = ConfigDict(extra="forbid")

    week_number: int = Field(ge=1, le=52)
    reason: AdaptationTriggerReason
    topic_count: int = Field(default=0, ge=0)


class AdaptationCheckRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum: CurriculumPlan
    progress_summary: CurriculumProgressSummary
    quiz_history: QuizHistorySummary | None = None
    expected_week_number: int | None = Field(default=None, ge=1, le=52)
    manual_trigger: bool = False
    trigger_note: str | None = Field(default=None, max_length=600)


class AdaptationDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adaptation_id: str = Field(default_factory=new_adaptation_id)
    user_id: str | None = Field(default=None, max_length=120)
    goal_id: str | None = Field(default=None, max_length=120)
    curriculum_id: str = Field(min_length=1, max_length=120)
    decision: AdaptationDecisionStatus
    should_replan: bool
    trigger_reason: AdaptationTriggerReason
    trigger_details: str = Field(min_length=1, max_length=800)
    signals: list[AdaptationSignal] = Field(default_factory=list)
    affected_weeks: list[AffectedWeek] = Field(default_factory=list)
    affected_topics: list[AffectedTopic] = Field(default_factory=list)
    flow: list[ReplanFlowStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class AdaptationReplanRequest(AdaptationCheckRequest):
    model_config = ConfigDict(extra="forbid")

    existing_resource_attachment: CurriculumResourceAttachmentResponse | None = None
    top_k: int = Field(default=2, ge=1, le=5)


class CurriculumDiff(BaseModel):
    model_config = ConfigDict(extra="forbid")

    changed_week_numbers: list[int] = Field(default_factory=list)
    preserved_week_numbers: list[int] = Field(default_factory=list)
    changed_topic_names: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1, max_length=1200)


class ResourceRefreshSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refreshed_week_numbers: list[int] = Field(default_factory=list)
    refreshed_topic_count: int = Field(default=0, ge=0)
    refreshed_topic_names: list[str] = Field(default_factory=list)
    used_existing_unaffected_resources: bool = False
    warnings: list[str] = Field(default_factory=list)


class CriticReviewSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: bool
    decision: str = Field(min_length=1, max_length=40)
    score: float = Field(ge=0.0, le=1.0)
    revision_instruction_count: int = Field(default=0, ge=0)
    warnings: list[str] = Field(default_factory=list)


class NotificationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=180)
    message: str = Field(min_length=1, max_length=1000)
    reason: AdaptationTriggerReason
    affected_weeks: list[int] = Field(default_factory=list)
    change_summary: str = Field(min_length=1, max_length=1200)
    created_at: datetime = Field(default_factory=utc_now)


class AdaptationLogPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adaptation_id: str = Field(min_length=1, max_length=120)
    curriculum_id: str = Field(min_length=1, max_length=120)
    trigger_reason: AdaptationTriggerReason
    decision: AdaptationDecisionStatus
    affected_weeks: list[int] = Field(default_factory=list)
    affected_topics: list[str] = Field(default_factory=list)
    critic_approved: bool | None = None
    created_at: datetime = Field(default_factory=utc_now)


class AdaptationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    adaptation_id: str = Field(default_factory=new_adaptation_id)
    user_id: str | None = Field(default=None, max_length=120)
    goal_id: str | None = Field(default=None, max_length=120)
    curriculum_id: str = Field(min_length=1, max_length=120)
    decision: AdaptationDecision
    curriculum_before: CurriculumPlan
    curriculum_after: CurriculumPlan | None = None
    curriculum_diff: CurriculumDiff | None = None
    resource_attachment: CurriculumResourceAttachmentResponse | None = None
    resource_refresh_summary: ResourceRefreshSummary | None = None
    critic_review: CriticReviewSummary | None = None
    notification: NotificationPayload | None = None
    adaptation_log: AdaptationLogPayload
    created_at: datetime = Field(default_factory=utc_now)


class AdaptationHistoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum_id: str = Field(min_length=1, max_length=120)
    adaptations: list[AdaptationResult] = Field(default_factory=list)


class AdaptationExampleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    result: AdaptationResult
