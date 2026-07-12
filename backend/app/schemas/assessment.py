from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.base import BaseSchema, Score, TimestampedDTO, VersionedDTO
from app.schemas.enums import AssessmentStatus, DifficultyLevel, QuestionType
from app.schemas.goal import LearnerProfile
from app.schemas.ids import AnswerId, AssessmentId, ConceptId, GoalId, QuestionId, RunId


class AssessmentQuestionDTO(BaseSchema):
    question_id: QuestionId
    question_type: QuestionType
    prompt: str = Field(min_length=1, max_length=800)
    options: list[str] = Field(default_factory=list, max_length=8)
    target_concepts: list[ConceptId] = Field(min_length=1, max_length=8)
    difficulty: DifficultyLevel


class ConceptEvidence(BaseSchema):
    concept_id: ConceptId
    score: Score
    evidence: list[str] = Field(default_factory=list, max_length=12)


class ConceptEvidenceUpdate(BaseSchema):
    concept_id: ConceptId
    score_delta: float = Field(ge=-1.0, le=1.0)
    evidence: str = Field(min_length=1, max_length=400)


class AssessmentAnswerCreate(BaseSchema):
    question_id: QuestionId
    answer_text: str | None = Field(default=None, max_length=1200)
    selected_options: list[str] = Field(default_factory=list, max_length=8)
    self_rating: int | None = Field(default=None, ge=1, le=5)


class AssessmentAnswerDTO(TimestampedDTO, VersionedDTO):
    answer_id: AnswerId
    assessment_session_id: AssessmentId
    goal_id: GoalId
    question: AssessmentQuestionDTO
    answer_text: str | None = Field(default=None, max_length=1200)
    selected_options: list[str] = Field(default_factory=list, max_length=8)
    self_rating: int | None = Field(default=None, ge=1, le=5)
    score: Score
    concept_scores: list[ConceptEvidenceUpdate] = Field(default_factory=list)
    feedback: str | None = Field(default=None, max_length=800)


class AssessmentSessionDTO(TimestampedDTO, VersionedDTO):
    assessment_session_id: AssessmentId
    goal_id: GoalId
    run_id: RunId
    status: AssessmentStatus
    question_count: int = Field(ge=0, le=20)
    confidence: Score
    concept_evidence: list[ConceptEvidence] = Field(default_factory=list)
    current_question: AssessmentQuestionDTO | None = None
    started_at: datetime
    completed_at: datetime | None = None
    termination_reason: str | None = Field(default=None, max_length=200)


class AssessmentAgentInput(BaseSchema):
    goal_text: str = Field(min_length=5, max_length=500)
    learner_profile: LearnerProfile
    prior_answers: list[AssessmentAnswerDTO] = Field(default_factory=list)
    target_concepts: list[ConceptId] = Field(min_length=1, max_length=20)
    current_confidence: Score
    question_count: int = Field(ge=0, le=20)


class AssessmentAgentOutput(BaseSchema):
    question: AssessmentQuestionDTO
    rationale: str = Field(min_length=1, max_length=800)
    estimated_information_gain: Score


class AssessmentScoreOutput(BaseSchema):
    answer_id: AnswerId | None = None
    score: Score
    concept_scores: list[ConceptEvidenceUpdate] = Field(min_length=1)
    feedback: str = Field(min_length=1, max_length=800)
    confidence_after_answer: Score


class AssessmentAnswerResponse(BaseSchema):
    session: AssessmentSessionDTO
    answer: AssessmentAnswerDTO
