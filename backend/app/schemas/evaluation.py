from __future__ import annotations

from pydantic import Field

from app.schemas.adaptation import AdaptationEventDTO
from app.schemas.assessment import AssessmentSessionDTO
from app.schemas.base import BaseSchema, Score, TimestampedDTO, VersionedDTO
from app.schemas.critic import CriticReviewDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.enums import EvaluationPassStatus
from app.schemas.goal import LearningGoalDTO
from app.schemas.ids import EvaluationReportId, GoalId, RunId
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.schemas.quiz import QuizAttemptDTO
from app.schemas.resource import ResourceAttachmentDTO


class EvaluationMetricScores(BaseSchema):
    curriculum_coverage: Score
    difficulty_alignment: Score
    pacing_balance: Score
    resource_relevance: Score
    resource_diversity: Score
    quiz_alignment: Score
    critic_coherence: Score
    workflow_completeness: Score
    adaptation_usefulness: Score | None = None


class EvaluationReportDTO(TimestampedDTO, VersionedDTO):
    evaluation_report_id: EvaluationReportId
    goal_id: GoalId
    run_id: RunId
    metric_scores: EvaluationMetricScores
    weights: dict[str, float] = Field(default_factory=dict)
    overall_score: Score
    pass_status: EvaluationPassStatus
    warnings: list[str] = Field(default_factory=list, max_length=20)
    recommendations: list[str] = Field(default_factory=list, max_length=20)
    artifact_ids: dict[str, str] = Field(default_factory=dict)


class EvaluationAgentInput(BaseSchema):
    goal: LearningGoalDTO
    assessment: AssessmentSessionDTO
    knowledge_map: KnowledgeMapDTO
    curriculum: CurriculumDTO
    resources: list[ResourceAttachmentDTO] = Field(default_factory=list)
    critic_review: CriticReviewDTO | None = None
    quiz_attempt: QuizAttemptDTO | None = None
    adaptation_event: AdaptationEventDTO | None = None


class EvaluationAgentOutput(BaseSchema):
    metric_scores: EvaluationMetricScores
    weighted_score: Score
    pass_status: EvaluationPassStatus
    warnings: list[str] = Field(default_factory=list, max_length=20)
    recommendations: list[str] = Field(default_factory=list, max_length=20)
