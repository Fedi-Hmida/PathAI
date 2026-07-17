from __future__ import annotations

from app.schemas.base import BaseSchema
from app.schemas.ids import (
    AttemptId,
    CriticReviewId,
    CurriculumId,
    EvaluationReportId,
    KnowledgeMapId,
    QuizId,
    RunId,
)


class WorkspaceRef(BaseSchema):
    """Pointer to a user's workspace, identified by its orchestration run."""

    run_id: RunId


class WorkspaceGenerationResult(BaseSchema):
    """Pointer to the caller's freshly (re)generated knowledge map,
    curriculum, critic review, evaluation report, and quiz + attempt."""

    knowledge_map_id: KnowledgeMapId
    curriculum_id: CurriculumId
    critic_review_id: CriticReviewId
    evaluation_report_id: EvaluationReportId
    quiz_id: QuizId
    quiz_attempt_id: AttemptId
