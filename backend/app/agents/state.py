from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.agents.constants import (
    DEFAULT_MAX_REVISIONS,
    GRAPH_VERSION,
    CriticDecision,
    JobStatus,
    ResourceRefreshScope,
    StageName,
    TraceStatus,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_run_id() -> str:
    return str(uuid4())


class GraphError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_name: str
    code: str
    message: str
    recoverable: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class GraphWarning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_name: str
    code: str
    message: str
    created_at: datetime = Field(default_factory=utc_now)


class TraceEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_name: str
    status: TraceStatus
    timestamp: datetime = Field(default_factory=utc_now)
    revision_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class CriticReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: CriticDecision
    approved: bool
    score: float = Field(ge=0.0, le=1.0)
    auto_approved: bool = False
    revision_instructions: str | None = None


class NodeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_name: str
    status: Literal["completed", "failed"]
    message: str


class GraphState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_version: str = GRAPH_VERSION
    run_id: str = Field(default_factory=new_run_id)
    user_id: str
    goal_id: str
    goal: str = Field(min_length=3, max_length=1000)
    timeline_weeks: int = Field(ge=1, le=52)
    hours_per_week: int = Field(ge=1, le=80)
    knowledge_map: dict[str, Any] = Field(default_factory=dict)
    curriculum: list[dict[str, Any]] = Field(default_factory=list)
    resources: list[dict[str, Any]] = Field(default_factory=list)
    progress: list[dict[str, Any]] = Field(default_factory=list)
    current_stage: StageName = "created"
    resource_refresh_scope: ResourceRefreshScope = "all"
    revision_count: int = Field(default=0, ge=0)
    max_revisions: int = Field(default=DEFAULT_MAX_REVISIONS, ge=0, le=10)
    critic_review: CriticReview | None = None
    job_status: JobStatus = "queued"
    errors: list[GraphError] = Field(default_factory=list)
    warnings: list[GraphWarning] = Field(default_factory=list)
    trace: list[TraceEvent] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def public_summary(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "user_id": self.user_id,
            "goal_id": self.goal_id,
            "current_stage": self.current_stage,
            "job_status": self.job_status,
            "revision_count": self.revision_count,
            "max_revisions": self.max_revisions,
            "critic_approved": self.critic_review.approved if self.critic_review else None,
            "auto_approved": self.critic_review.auto_approved if self.critic_review else False,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "trace_count": len(self.trace),
        }
