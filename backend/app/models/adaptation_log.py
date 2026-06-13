from datetime import datetime
from typing import Literal

from beanie import Document
from pydantic import ConfigDict, Field
from pymongo import ASCENDING, IndexModel

from app.models.common import utc_now

AdaptationTrigger = Literal[
    "behind_schedule",
    "low_quiz_score",
    "stuck_flag",
    "ahead_of_schedule",
    "manual_request",
]


class AdaptationLogDocument(Document):
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(min_length=1)
    goal_id: str = Field(min_length=1)
    triggered_at: datetime = Field(default_factory=utc_now)
    trigger_reason: AdaptationTrigger
    trigger_details: str = Field(min_length=1, max_length=1200)
    weeks_affected: list[int] = Field(default_factory=list)
    curriculum_before: dict[str, object] | None = None
    curriculum_after: dict[str, object] | None = None
    agent_reasoning: str | None = Field(default=None, max_length=4000)

    class Settings:
        name = "adaptation_logs"
        indexes = [
            IndexModel(
                [
                    ("user_id", ASCENDING),
                    ("goal_id", ASCENDING),
                    ("triggered_at", ASCENDING),
                ]
            ),
        ]
