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


class LLMRunBudgetSummary(BaseSchema):
    """Redacted per-run LLM call/wall-clock budget summary (RULES.md §17.1.4).

    Mirrors `RunScopedBudgetObserver.safe_summary()`'s shape exactly — no
    prompt content, no raw provider error text, no schema names. Only present
    when at least one LLM agent actually ran during this generation; a fully
    deterministic run carries no summary at all.
    """

    llm_call_count: int
    max_llm_calls: int
    elapsed_seconds: float
    max_wall_clock_seconds: float
    exhausted: bool
    exhaustion_reason: str | None = None


class WorkspaceGenerationResult(BaseSchema):
    """Pointer to the caller's freshly (re)generated knowledge map,
    curriculum, critic review, evaluation report, and quiz + attempt."""

    knowledge_map_id: KnowledgeMapId
    curriculum_id: CurriculumId
    critic_review_id: CriticReviewId
    evaluation_report_id: EvaluationReportId
    quiz_id: QuizId
    quiz_attempt_id: AttemptId
    llm_budget_summary: LLMRunBudgetSummary | None = None
