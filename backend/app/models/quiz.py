from datetime import datetime
from typing import Literal

from beanie import Document
from pydantic import BaseModel, ConfigDict, Field
from pymongo import ASCENDING, IndexModel

from app.models.common import new_uuid, utc_now

QuestionType = Literal["mcq", "short_answer", "true_false"]


class QuizQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(default_factory=new_uuid)
    type: QuestionType
    prompt: str = Field(min_length=1, max_length=1200)
    options: list[str] = Field(default_factory=list, max_length=6)
    correct_answer: str | None = Field(default=None, max_length=1000)
    rubric: str | None = Field(default=None, max_length=1200)


class QuizDocument(Document):
    model_config = ConfigDict(extra="forbid")

    quiz_id: str = Field(default_factory=new_uuid)
    user_id: str = Field(min_length=1)
    goal_id: str = Field(min_length=1)
    week_number: int = Field(ge=1, le=52)
    topic_ids: list[str] = Field(default_factory=list)
    questions: list[QuizQuestion] = Field(default_factory=list)
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    feedback: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None

    class Settings:
        name = "quizzes"
        indexes = [
            IndexModel([("quiz_id", ASCENDING)], unique=True),
            IndexModel(
                [
                    ("user_id", ASCENDING),
                    ("goal_id", ASCENDING),
                    ("week_number", ASCENDING),
                ]
            ),
        ]
