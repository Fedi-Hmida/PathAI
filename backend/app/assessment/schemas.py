from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.assessment.constants import (
    DEFAULT_MAX_QUESTIONS,
    DEFAULT_USER_ID,
    MAX_ASSESSMENT_QUESTIONS,
    MIN_ASSESSMENT_QUESTIONS,
    MIN_QUESTIONS_FOR_CONFIDENCE,
    AssessmentQuestionSource,
    AssessmentQuestionType,
    AssessmentSignal,
    AssessmentStatus,
    DifficultyLevel,
)


class GoalIntakeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal: str = Field(min_length=3, max_length=1000)
    timeline_weeks: int = Field(ge=1, le=52)
    hours_per_week: int = Field(ge=1, le=80)
    target_level: DifficultyLevel = "intermediate"
    user_id: str = Field(default=DEFAULT_USER_ID, min_length=1, max_length=120)
    goal_id: str | None = Field(default=None, min_length=1, max_length=120)
    max_questions: int = Field(
        default=DEFAULT_MAX_QUESTIONS,
        ge=MIN_ASSESSMENT_QUESTIONS,
        le=MAX_ASSESSMENT_QUESTIONS,
    )

    @field_validator("goal")
    @classmethod
    def normalize_goal(cls, value: str) -> str:
        return " ".join(value.strip().split())


class AssessmentQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1, max_length=120)
    topic: str = Field(min_length=1, max_length=120)
    prompt: str = Field(min_length=5, max_length=1200)
    question_type: AssessmentQuestionType = "short_answer"
    difficulty: DifficultyLevel
    options: list[str] = Field(default_factory=list, max_length=6)
    expected_concepts: list[str] = Field(default_factory=list, min_length=1, max_length=8)
    skill_tags: list[str] = Field(default_factory=list, max_length=8)
    source: AssessmentQuestionSource = "question_bank"


class GeneratedAssessmentQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=5, max_length=1200)
    topic: str = Field(min_length=1, max_length=120)
    question_type: AssessmentQuestionType = "short_answer"
    difficulty: DifficultyLevel
    options: list[str] = Field(default_factory=list, max_length=6)
    expected_concepts: list[str] = Field(default_factory=list, min_length=1, max_length=8)
    skill_tags: list[str] = Field(default_factory=list, max_length=8)


class AnswerSubmissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(default="", max_length=2000)

    @field_validator("answer")
    @classmethod
    def normalize_answer(cls, value: str) -> str:
        return " ".join(value.strip().split())


class AnswerEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    topic: str
    difficulty: DifficultyLevel
    answer: str
    score: float = Field(ge=0.0, le=1.0)
    signal: AssessmentSignal
    matched_concepts: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    is_idk: bool = False
    feedback: str = Field(min_length=1, max_length=700)
    created_at: datetime


class LLMAnswerEvaluationDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0.0, le=1.0)
    signal: AssessmentSignal
    matched_concepts: list[str] = Field(default_factory=list)
    missing_concepts: list[str] = Field(default_factory=list)
    feedback: str = Field(min_length=1, max_length=700)


class KnowledgeMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strong: list[str] = Field(default_factory=list)
    weak: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    recommended_level: DifficultyLevel
    confidence_score: float = Field(ge=0.0, le=1.0)
    assessment_notes: list[str] = Field(default_factory=list)


class KnowledgeMapDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strong: list[str] = Field(default_factory=list)
    weak: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    recommended_level: DifficultyLevel
    confidence_score: float = Field(ge=0.0, le=1.0)
    assessment_notes: list[str] = Field(default_factory=list)


class AssessmentProgress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answered_count: int = Field(ge=0)
    asked_count: int = Field(ge=0)
    max_questions: int = Field(ge=MIN_ASSESSMENT_QUESTIONS, le=MAX_ASSESSMENT_QUESTIONS)
    min_questions_for_confidence: int = Field(default=MIN_QUESTIONS_FOR_CONFIDENCE, ge=1)
    confidence_score: float = Field(ge=0.0, le=1.0)
    current_difficulty: DifficultyLevel
    status: AssessmentStatus
    enough_evidence: bool = False


class AssessmentSessionState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    user_id: str = DEFAULT_USER_ID
    goal_id: str | None = None
    goal: str = Field(min_length=3, max_length=1000)
    timeline_weeks: int = Field(ge=1, le=52)
    hours_per_week: int = Field(ge=1, le=80)
    target_level: DifficultyLevel
    question_index: int = Field(default=1, ge=0)
    max_questions: int = Field(ge=MIN_ASSESSMENT_QUESTIONS, le=MAX_ASSESSMENT_QUESTIONS)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: AssessmentStatus = "in_progress"
    current_difficulty: DifficultyLevel
    questions: list[AssessmentQuestion] = Field(default_factory=list)
    answers: list[AnswerEvaluation] = Field(default_factory=list)
    knowledge_map: KnowledgeMap | None = None
    assessment_notes: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @property
    def progress(self) -> AssessmentProgress:
        return AssessmentProgress(
            answered_count=len(self.answers),
            asked_count=len(self.questions),
            max_questions=self.max_questions,
            confidence_score=self.confidence_score,
            current_difficulty=self.current_difficulty,
            status=self.status,
            enough_evidence=self.confidence_score >= 0.82
            and len(self.answers) >= MIN_QUESTIONS_FOR_CONFIDENCE,
        )


class FinalAssessmentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    status: Annotated[AssessmentStatus, Field(pattern="^completed$")] = "completed"
    knowledge_map: KnowledgeMap
    progress: AssessmentProgress


class StartAssessmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: AssessmentSessionState
    next_question: AssessmentQuestion


class SubmitAnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: AssessmentSessionState
    evaluation: AnswerEvaluation | None = None
    next_question: AssessmentQuestion | None = None
    result: FinalAssessmentResult | None = None


class AssessmentSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: AssessmentSessionState


class FinalizeAssessmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session: AssessmentSessionState
    result: FinalAssessmentResult
