from datetime import datetime

from beanie import Document
from pydantic import ConfigDict, Field, field_validator
from pymongo import ASCENDING, IndexModel

from app.models.common import LearningGoal, utc_now


class UserProfileDocument(Document):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=120)
    university_id: str | None = Field(default=None, max_length=80)
    timezone: str = Field(default="Africa/Tunis", max_length=80)
    consent_version: str | None = Field(default=None, max_length=40)
    goals: list[LearningGoal] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized:
            raise ValueError("email must contain @")
        return normalized

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("goals.goal_id", ASCENDING)]),
        ]
