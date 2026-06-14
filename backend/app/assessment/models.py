from datetime import datetime
from typing import Any

from beanie import Document
from pydantic import ConfigDict, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.assessment.constants import AssessmentStatus, DifficultyLevel, new_uuid, utc_now
from app.assessment.schemas import AnswerEvaluation, AssessmentQuestion, KnowledgeMap


class AssessmentSessionDocument(Document):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(default_factory=new_uuid)
    user_id: str = Field(default="demo-user", min_length=1, max_length=120)
    goal_id: str | None = Field(default=None, max_length=120)
    goal: str = Field(min_length=3, max_length=1000)
    timeline_weeks: int = Field(ge=1, le=52)
    hours_per_week: int = Field(ge=1, le=80)
    target_level: DifficultyLevel
    question_index: int = Field(default=1, ge=0)
    max_questions: int = Field(default=8, ge=3, le=12)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: AssessmentStatus = "in_progress"
    current_difficulty: DifficultyLevel
    questions: list[AssessmentQuestion] = Field(default_factory=list)
    answers: list[AnswerEvaluation] = Field(default_factory=list)
    knowledge_map: KnowledgeMap | None = None
    assessment_notes: list[str] = Field(default_factory=list)
    result: dict[str, Any] | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "assessment_sessions"
        indexes = [
            IndexModel([("session_id", ASCENDING)], unique=True),
            IndexModel([("user_id", ASCENDING), ("status", ASCENDING)]),
            IndexModel([("goal_id", ASCENDING), ("created_at", DESCENDING)]),
        ]
