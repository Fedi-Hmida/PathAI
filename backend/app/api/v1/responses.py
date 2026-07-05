from __future__ import annotations

from app.schemas.base import BaseSchema
from app.schemas.dashboard import DashboardPayload
from app.schemas.enums import ExecutionMode
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


class DemoLoadFixturesResponse(BaseSchema):
    message: str
    mode: ExecutionMode
    deterministic: bool
    run_id: RunId
    goal_id: GoalId
    assessment_id: AssessmentId
    knowledge_map_id: KnowledgeMapId
    curriculum_id: CurriculumId
    progress_id: ProgressId
    quiz_id: QuizId
    quiz_attempt_id: AttemptId
    adaptation_id: AdaptationId
    critic_id: CriticReviewId
    evaluation_id: EvaluationReportId
    dashboard_payload: DashboardPayload | None = None
