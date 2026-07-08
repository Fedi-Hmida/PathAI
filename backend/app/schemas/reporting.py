from __future__ import annotations

from pydantic import Field

from app.schemas.base import BaseSchema, Score
from app.schemas.enums import EvaluationPassStatus, OrchestrationStatus
from app.schemas.ids import ConceptId, GoalId, RunId


class ReportingSummaryDTO(BaseSchema):
    run_id: RunId
    goal_id: GoalId
    status: OrchestrationStatus
    deterministic: bool
    demo_ready: bool
    artifact_ids: dict[str, str] = Field(default_factory=dict)
    overall_quality_score: Score | None = None
    evaluation_pass_status: EvaluationPassStatus | None = None
    weak_concepts: list[ConceptId] = Field(default_factory=list, max_length=20)
    current_topic: str | None = Field(default=None, max_length=220)
    next_action: str | None = Field(default=None, max_length=500)
    critic_warnings: list[str] = Field(default_factory=list, max_length=10)
    adaptation_warnings: list[str] = Field(default_factory=list, max_length=10)
    readiness_notes: list[str] = Field(default_factory=list, max_length=10)
