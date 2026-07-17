from __future__ import annotations

from app.schemas.base import BaseSchema
from app.schemas.ids import CriticReviewId, CurriculumId, EvaluationReportId, KnowledgeMapId, RunId


class WorkspaceRef(BaseSchema):
    """Pointer to a user's workspace, identified by its orchestration run."""

    run_id: RunId


class WorkspaceGenerationResult(BaseSchema):
    """Pointer to the caller's freshly (re)generated knowledge map,
    curriculum, critic review, and evaluation report."""

    knowledge_map_id: KnowledgeMapId
    curriculum_id: CurriculumId
    critic_review_id: CriticReviewId
    evaluation_report_id: EvaluationReportId
