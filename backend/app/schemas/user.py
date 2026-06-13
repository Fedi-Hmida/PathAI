from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.learning import LearningGoalRead


class UserProfileRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str | None = None
    email: str = Field(min_length=3, max_length=320)
    name: str = Field(min_length=1, max_length=120)
    university_id: str | None = None
    timezone: str
    consent_version: str | None = None
    goals: list[LearningGoalRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
