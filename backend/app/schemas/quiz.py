from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.quiz import QuestionType


class QuizQuestionSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    type: QuestionType
    prompt: str = Field(min_length=1, max_length=1200)
    options: list[str] = Field(default_factory=list, max_length=6)
    correct_answer: str | None = Field(default=None, max_length=1000)
    rubric: str | None = Field(default=None, max_length=1200)


class QuizRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quiz_id: str
    user_id: str
    goal_id: str
    week_number: int
    topic_ids: list[str] = Field(default_factory=list)
    questions: list[QuizQuestionSchema] = Field(default_factory=list)
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    feedback: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
