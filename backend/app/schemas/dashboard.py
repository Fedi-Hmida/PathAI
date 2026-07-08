from __future__ import annotations

from pydantic import Field

from app.schemas.base import BaseSchema, Score
from app.schemas.enums import (
    AdaptationStatus,
    AssessmentStatus,
    CriticPassStatus,
    EvaluationPassStatus,
    ExecutionMode,
    GoalStatus,
    OrchestrationStatus,
)
from app.schemas.ids import ConceptId, CurriculumId, GoalId, RunId


class RunSummary(BaseSchema):
    run_id: RunId
    status: OrchestrationStatus
    mode: ExecutionMode
    current_node: str | None = Field(default=None, max_length=120)


class GoalSummary(BaseSchema):
    goal_id: GoalId
    text: str = Field(min_length=5, max_length=500)
    status: GoalStatus


class KnowledgeMapSummary(BaseSchema):
    strong_concepts: list[ConceptId] = Field(default_factory=list)
    weak_concepts: list[ConceptId] = Field(default_factory=list)
    summary: str | None = Field(default=None, max_length=1000)


class AssessmentSummary(BaseSchema):
    assessment_session_id: str
    status: AssessmentStatus
    question_count: int = Field(ge=0, le=100)
    confidence: Score
    termination_reason: str | None = Field(default=None, max_length=200)


class CurriculumWeekSummary(BaseSchema):
    week_number: int = Field(ge=1, le=52)
    theme: str = Field(min_length=1, max_length=220)
    topic_titles: list[str] = Field(default_factory=list, max_length=12)


class CurriculumSummary(BaseSchema):
    active_curriculum_id: CurriculumId | None = None
    title: str | None = Field(default=None, max_length=220)
    weeks: list[CurriculumWeekSummary] = Field(default_factory=list)


class ProgressSummary(BaseSchema):
    completion_percentage: int = Field(ge=0, le=100)
    current_topic: str | None = Field(default=None, max_length=220)
    weak_concepts: list[ConceptId] = Field(default_factory=list)
    next_action_label: str | None = Field(default=None, max_length=220)
    next_action_reason: str | None = Field(default=None, max_length=500)


class QuizSummary(BaseSchema):
    latest_score: Score | None = None
    weak_concepts: list[ConceptId] = Field(default_factory=list)


class ResourcesSummary(BaseSchema):
    total_attached: int = Field(ge=0)
    average_relevance: Score | None = None
    resource_type_diversity: Score | None = None


class AdaptationSummary(BaseSchema):
    recent_events: list[str] = Field(default_factory=list, max_length=10)
    latest_status: AdaptationStatus | None = None


class CriticSummary(BaseSchema):
    overall_score: Score | None = None
    pass_status: CriticPassStatus | None = None
    issue_count: int = Field(default=0, ge=0, le=100)
    top_issues: list[str] = Field(default_factory=list, max_length=5)


class EvaluationSummary(BaseSchema):
    overall_score: Score | None = None
    pass_status: EvaluationPassStatus | None = None


class DashboardUIFlags(BaseSchema):
    show_adaptation_alert: bool = False
    requires_user_input: bool = False


class NavigationSummary(BaseSchema):
    artifact_ids: dict[str, str] = Field(default_factory=dict)


class DashboardPayload(BaseSchema):
    run_summary: RunSummary
    goal_summary: GoalSummary
    navigation_summary: NavigationSummary = Field(default_factory=NavigationSummary)
    assessment_summary: AssessmentSummary | None = None
    knowledge_map_summary: KnowledgeMapSummary | None = None
    curriculum_summary: CurriculumSummary | None = None
    progress_summary: ProgressSummary | None = None
    quiz_summary: QuizSummary | None = None
    resources_summary: ResourcesSummary | None = None
    adaptation_summary: AdaptationSummary | None = None
    critic_summary: CriticSummary | None = None
    evaluation_summary: EvaluationSummary | None = None
    ui_flags: DashboardUIFlags = Field(default_factory=DashboardUIFlags)
