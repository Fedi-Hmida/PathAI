from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.adaptation_log import AdaptationTrigger


class AdaptationLogRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str
    goal_id: str
    triggered_at: datetime
    trigger_reason: AdaptationTrigger
    trigger_details: str
    weeks_affected: list[int] = Field(default_factory=list)
    curriculum_before: dict[str, object] | None = None
    curriculum_after: dict[str, object] | None = None
    agent_reasoning: str | None = None
