from datetime import datetime

from beanie import Document
from pydantic import ConfigDict, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.assessment.schemas import KnowledgeMap
from app.curriculum.constants import CurriculumSource, CurriculumStatus, new_uuid, utc_now
from app.curriculum.schemas import CurriculumValidationIssue, CurriculumWeek, DifficultyProgression


class CurriculumDocument(Document):
    model_config = ConfigDict(extra="forbid")

    curriculum_id: str = Field(default_factory=new_uuid)
    user_id: str = Field(default="demo-user", min_length=1, max_length=120)
    goal_id: str | None = Field(default=None, max_length=120)
    assessment_session_id: str | None = Field(default=None, max_length=120)
    goal: str = Field(min_length=3, max_length=1000)
    timeline_weeks: int = Field(ge=1, le=52)
    hours_per_week: int = Field(ge=1, le=80)
    knowledge_map: KnowledgeMap
    weeks: list[CurriculumWeek] = Field(default_factory=list)
    total_hours: float = Field(ge=1.0)
    difficulty_progression: DifficultyProgression
    generation_notes: list[str] = Field(default_factory=list)
    source: CurriculumSource = "deterministic"
    status: CurriculumStatus = "generated"
    validation_issues: list[CurriculumValidationIssue] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "curricula"
        indexes = [
            IndexModel([("curriculum_id", ASCENDING)], unique=True),
            IndexModel([("user_id", ASCENDING), ("goal_id", ASCENDING)]),
            IndexModel([("assessment_session_id", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)]),
        ]
