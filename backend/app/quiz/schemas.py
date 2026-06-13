from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.curriculum.schemas import CurriculumPlan
from app.quiz.constants import (
    DEFAULT_QUESTION_COUNT,
    MAX_QUESTION_COUNT,
    QuizQuestionType,
    new_attempt_id,
    new_question_id,
    new_quiz_id,
    utc_now,
)
from app.rag.schemas import CurriculumResourceAttachmentResponse


class QuizGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum: CurriculumPlan
    week_number: int = Field(ge=1, le=52)
    resource_attachment: CurriculumResourceAttachmentResponse | None = None
    question_count: int = Field(
        default=DEFAULT_QUESTION_COUNT,
        ge=1,
        le=MAX_QUESTION_COUNT,
    )
    use_mock_llm: bool = False


class QuizOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    option_id: str = Field(min_length=1, max_length=10)
    text: str = Field(min_length=1, max_length=300)


class QuizQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(default_factory=new_question_id)
    type: QuizQuestionType
    prompt: str = Field(min_length=1, max_length=1200)
    options: list[QuizOption] = Field(default_factory=list, max_length=6)
    correct_answer: str = Field(min_length=1, max_length=1000)
    explanation: str = Field(min_length=1, max_length=1000)
    difficulty: str = Field(min_length=1, max_length=40)
    topic_id: str | None = Field(default=None, max_length=120)
    topic_name: str = Field(min_length=1, max_length=180)

    @model_validator(mode="after")
    def validate_options_for_question_type(self) -> "QuizQuestion":
        if self.type == "multiple_choice" and len(self.options) < 2:
            raise ValueError("Multiple-choice questions require at least two options.")
        return self


class Quiz(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quiz_id: str = Field(default_factory=new_quiz_id)
    curriculum_id: str = Field(min_length=1, max_length=120)
    goal_id: str | None = Field(default=None, max_length=120)
    user_id: str | None = Field(default=None, max_length=120)
    week_number: int = Field(ge=1, le=52)
    topic_names: list[str] = Field(default_factory=list)
    questions: list[QuizQuestion] = Field(default_factory=list, min_length=1)
    created_at: datetime = Field(default_factory=utc_now)


class QuizGenerateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quiz: Quiz


class QuizAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1, max_length=120)
    answer: str = Field(min_length=0, max_length=1000)


class QuizSubmissionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answers: list[QuizAnswer] = Field(default_factory=list, min_length=1)


class QuizFeedbackItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1, max_length=120)
    correct: bool
    learner_answer: str
    correct_answer: str
    explanation: str
    topic_name: str


class QuizAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempt_id: str = Field(default_factory=new_attempt_id)
    quiz_id: str = Field(min_length=1, max_length=120)
    curriculum_id: str = Field(min_length=1, max_length=120)
    week_number: int = Field(ge=1, le=52)
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    feedback: list[QuizFeedbackItem] = Field(default_factory=list)
    submitted_at: datetime = Field(default_factory=utc_now)


class QuizResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quiz_id: str
    curriculum_id: str
    week_number: int
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    best_score: float = Field(ge=0.0, le=1.0)
    low_score_signal: bool
    attempt: QuizAttempt


class QuizHistorySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    curriculum_id: str
    attempts: list[QuizAttempt] = Field(default_factory=list)
    best_score: float | None = Field(default=None, ge=0.0, le=1.0)
    average_score: float | None = Field(default=None, ge=0.0, le=1.0)
    low_score_count: int = Field(default=0, ge=0)


class QuizExampleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quiz: Quiz
    result: QuizResult
