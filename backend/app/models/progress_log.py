from datetime import datetime
from typing import Literal

from beanie import Document
from pydantic import ConfigDict, Field
from pymongo import ASCENDING, IndexModel

from app.models.common import utc_now

ProgressEvent = Literal[
    "marked_done",
    "marked_stuck",
    "marked_in_progress",
    "quiz_completed",
    "resource_viewed",
]


class ProgressLogDocument(Document):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)
    goal_id: str = Field(min_length=1)
    week_number: int = Field(ge=1, le=52)
    topic_id: str | None = None
    topic: str = Field(min_length=1, max_length=180)
    event: ProgressEvent
    value: dict[str, object] = Field(default_factory=dict)
    logged_at: datetime = Field(default_factory=utc_now)

    class Settings:
        name = "progress_logs"
        indexes = [
            IndexModel(
                [
                    ("user_id", ASCENDING),
                    ("goal_id", ASCENDING),
                    ("week_number", ASCENDING),
                    ("logged_at", ASCENDING),
                ]
            ),
        ]
