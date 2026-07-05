from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.base import (
    BaseSchema,
    Score,
    TimestampedDTO,
    TraceMetadata,
    VersionedDTO,
    WorkflowError,
    WorkflowWarning,
)
from app.schemas.enums import (
    ExecutionMode,
    NodeResultStatus,
    OrchestrationRunStatus,
    OrchestrationStatus,
)
from app.schemas.ids import (
    AdaptationId,
    AssessmentId,
    AttemptId,
    CriticReviewId,
    CurriculumId,
    EvaluationReportId,
    GoalId,
    KnowledgeMapId,
    ProgressId,
    QuizId,
    RunId,
)


class WorkflowState(BaseSchema):
    run_id: RunId
    goal_id: GoalId | None = None
    assessment_session_id: AssessmentId | None = None
    knowledge_map_id: KnowledgeMapId | None = None
    curriculum_id: CurriculumId | None = None
    progress_state_id: ProgressId | None = None
    quiz_id: QuizId | None = None
    quiz_attempt_id: AttemptId | None = None
    adaptation_event_ids: list[AdaptationId] = Field(default_factory=list)
    critic_review_id: CriticReviewId | None = None
    evaluation_report_id: EvaluationReportId | None = None
    current_node: str | None = Field(default=None, max_length=120)
    status: OrchestrationStatus
    mode: ExecutionMode = ExecutionMode.INTERACTIVE
    pending_user_action: str | None = Field(default=None, max_length=200)
    assessment_question_count: int = Field(default=0, ge=0, le=20)
    assessment_confidence: Score = 0.0
    critic_revision_attempts: int = Field(default=0, ge=0, le=10)
    repeated_stuck_count: int = Field(default=0, ge=0, le=20)
    quiz_score: Score | None = None
    errors: list[WorkflowError] = Field(default_factory=list)
    warnings: list[WorkflowWarning] = Field(default_factory=list)
    node_attempts: dict[str, int] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    trace_metadata: TraceMetadata = Field(default_factory=TraceMetadata)


class WorkflowNodeEvent(BaseSchema):
    run_id: RunId
    node_name: str = Field(min_length=1, max_length=120)
    status: NodeResultStatus
    attempt_count: int = Field(default=1, ge=1, le=20)
    message: str | None = Field(default=None, max_length=500)
    created_at: datetime
    errors: list[WorkflowError] = Field(default_factory=list)
    warnings: list[WorkflowWarning] = Field(default_factory=list)


class OrchestrationRunCreate(BaseSchema):
    goal_id: GoalId | None = None
    mode: ExecutionMode = ExecutionMode.INTERACTIVE
    client_request_id: str | None = Field(default=None, max_length=120)


class OrchestrationRunDTO(TimestampedDTO, VersionedDTO):
    run_id: RunId
    goal_id: GoalId | None = None
    workflow_version: str = Field(min_length=1, max_length=40)
    status: OrchestrationRunStatus
    current_node: str | None = Field(default=None, max_length=120)
    completed_nodes: list[str] = Field(default_factory=list)
    failed_nodes: list[str] = Field(default_factory=list)
    node_events: list[WorkflowNodeEvent] = Field(default_factory=list)
    artifact_ids: dict[str, str] = Field(default_factory=dict)
    started_at: datetime
    completed_at: datetime | None = None
    errors: list[WorkflowError] = Field(default_factory=list)
    warnings: list[WorkflowWarning] = Field(default_factory=list)


class OrchestrationStatusResponse(BaseSchema):
    run_id: RunId
    status: OrchestrationStatus
    current_node: str | None = Field(default=None, max_length=120)
    requires_user_input: bool = False
