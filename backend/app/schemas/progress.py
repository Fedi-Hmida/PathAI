from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.progress_log import ProgressEvent


class ProgressUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goal_id: str = Field(min_length=1)
    week_number: int = Field(ge=1, le=52)
    topic_id: str | None = None
    topic: str = Field(min_length=1, max_length=180)
    event: ProgressEvent
    value: dict[str, object] = Field(default_factory=dict)


class ProgressLogRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    goal_id: str
    week_number: int
    topic_id: str | None = None
    topic: str
    event: ProgressEvent
    value: dict[str, object]
    logged_at: datetime
