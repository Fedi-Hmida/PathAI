from __future__ import annotations

from datetime import UTC, datetime
from typing import NotRequired, TypedDict, cast

from app.schemas.base import TraceMetadata, WorkflowError, WorkflowWarning
from app.schemas.enums import CriticPassStatus, ExecutionMode, OrchestrationStatus
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
from app.schemas.orchestration import WorkflowState


class GraphState(TypedDict):
    run_id: RunId
    status: OrchestrationStatus
    mode: ExecutionMode
    errors: list[WorkflowError]
    warnings: list[WorkflowWarning]
    node_attempts: dict[str, int]
    created_at: datetime
    updated_at: datetime
    trace_metadata: TraceMetadata
    goal_id: NotRequired[GoalId | None]
    assessment_session_id: NotRequired[AssessmentId | None]
    knowledge_map_id: NotRequired[KnowledgeMapId | None]
    curriculum_id: NotRequired[CurriculumId | None]
    progress_state_id: NotRequired[ProgressId | None]
    quiz_id: NotRequired[QuizId | None]
    quiz_attempt_id: NotRequired[AttemptId | None]
    adaptation_event_ids: NotRequired[list[AdaptationId]]
    critic_review_id: NotRequired[CriticReviewId | None]
    critic_pass_status: NotRequired[CriticPassStatus | None]
    critic_recommendations: NotRequired[list[str]]
    evaluation_report_id: NotRequired[EvaluationReportId | None]
    current_node: NotRequired[str | None]
    pending_user_action: NotRequired[str | None]
    assessment_question_count: NotRequired[int]
    assessment_confidence: NotRequired[float]
    critic_revision_attempts: NotRequired[int]
    repeated_stuck_count: NotRequired[int]
    quiz_score: NotRequired[float | None]
    completed_at: NotRequired[datetime | None]


def build_initial_workflow_state(
    *,
    run_id: RunId,
    goal_id: GoalId | None,
    mode: ExecutionMode = ExecutionMode.DEMO,
    created_at: datetime | None = None,
) -> WorkflowState:
    now = created_at or _now()
    return WorkflowState(
        run_id=run_id,
        goal_id=goal_id,
        current_node=None,
        status=OrchestrationStatus.QUEUED,
        mode=mode,
        assessment_question_count=0,
        assessment_confidence=0.0,
        critic_pass_status=None,
        critic_recommendations=[],
        critic_revision_attempts=0,
        repeated_stuck_count=0,
        quiz_score=None,
        errors=[],
        warnings=[],
        node_attempts={},
        created_at=now,
        updated_at=now,
        completed_at=None,
        trace_metadata=TraceMetadata(run_id=run_id),
    )


def workflow_state_to_graph_state(state: WorkflowState) -> GraphState:
    return cast(GraphState, state.model_dump(mode="python"))


def graph_state_to_workflow_state(state: GraphState) -> WorkflowState:
    return WorkflowState.model_validate(state)


def merge_state(state: GraphState, **changes: object) -> GraphState:
    payload = dict(state)
    payload.update(changes)
    payload["updated_at"] = changes.get("updated_at", _now())
    return workflow_state_to_graph_state(WorkflowState.model_validate(payload))


def increment_node_attempt(state: GraphState, node_name: str) -> GraphState:
    attempts = dict(state.get("node_attempts", {}))
    attempts[node_name] = attempts.get(node_name, 0) + 1
    return merge_state(state, node_attempts=attempts)


def _now() -> datetime:
    return datetime.now(tz=UTC)
