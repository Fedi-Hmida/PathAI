from __future__ import annotations

from pydantic import Field

from app.schemas.base import BaseSchema, Score, TimestampedDTO, VersionedDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.enums import CriticPassStatus
from app.schemas.ids import CriticReviewId, CurriculumId, GoalId, RunId
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.schemas.resource import ResourceAttachmentDTO


class CriticDimensionScores(BaseSchema):
    coverage: Score
    pacing: Score
    resource_relevance: Score
    assessment_alignment: Score
    quiz_readiness: Score | None = None


class CriticReviewDTO(TimestampedDTO, VersionedDTO):
    critic_review_id: CriticReviewId
    goal_id: GoalId
    curriculum_id: CurriculumId
    run_id: RunId
    overall_score: Score
    pass_status: CriticPassStatus
    dimension_scores: CriticDimensionScores
    strengths: list[str] = Field(default_factory=list, max_length=20)
    issues: list[str] = Field(default_factory=list, max_length=20)
    revision_recommendations: list[str] = Field(default_factory=list, max_length=20)
    revision_attempt: int | None = Field(default=None, ge=0, le=10)


class CriticAgentInput(BaseSchema):
    goal_text: str = Field(min_length=5, max_length=500)
    knowledge_map: KnowledgeMapDTO
    curriculum: CurriculumDTO
    resource_attachments: list[ResourceAttachmentDTO] = Field(default_factory=list)
    rubric_weights: dict[str, float] = Field(default_factory=dict)


class CriticAgentOutput(BaseSchema):
    overall_score: Score
    pass_status: CriticPassStatus
    dimension_scores: CriticDimensionScores
    strengths: list[str] = Field(default_factory=list, max_length=20)
    issues: list[str] = Field(default_factory=list, max_length=20)
    revision_recommendations: list[str] = Field(default_factory=list, max_length=20)
