from datetime import datetime
from typing import Literal

from beanie import Document
from pydantic import ConfigDict, Field
from pymongo import ASCENDING, IndexModel

from app.models.common import new_uuid, utc_now

GenerationJobType = Literal["initial_curriculum", "manual_replan", "adapter_replan"]
GenerationJobStatus = Literal["queued", "running", "completed", "failed", "failed_persist"]


class GenerationJobDocument(Document):
    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(default_factory=new_uuid)
    user_id: str = Field(min_length=1)
    goal_id: str = Field(min_length=1)
    run_id: str | None = None
    type: GenerationJobType
    status: GenerationJobStatus = "queued"
    current_node: str | None = Field(default=None, max_length=80)
    progress_percent: int = Field(default=0, ge=0, le=100)
    error_code: str | None = Field(default=None, max_length=80)
    user_safe_message: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None

    class Settings:
        name = "generation_jobs"
        indexes = [
            IndexModel([("job_id", ASCENDING)], unique=True),
            IndexModel([("user_id", ASCENDING), ("goal_id", ASCENDING), ("status", ASCENDING)]),
        ]
