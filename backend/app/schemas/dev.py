from pydantic import BaseModel, Field

from app.agents.constants import DEFAULT_MAX_REVISIONS, NodeName
from app.schemas.learning import LearningGoalCreate


class RegisteredModelsResponse(BaseModel):
    models: list[str] = Field(default_factory=list)


class GoalValidationResponse(BaseModel):
    valid: bool = True
    goal: LearningGoalCreate
    message: str


class MockStructuredLLMRequest(BaseModel):
    prompt_name: str = Field(default="llm_health_check")
    context: str = Field(default="Offline mock validation for Phase 2.", max_length=1000)


class GraphDefinitionResponse(BaseModel):
    graph_version: str
    nodes: list[str]
    edges: list[dict[str, str]]
    conditional_routes: dict[str, str]
    default_max_revisions: int
    checkpoint_strategy: str
    real_llm_calls: bool
    database_writes: bool


class GraphDemoRunRequest(BaseModel):
    user_id: str = Field(default="dev-user")
    goal_id: str = Field(default="dev-goal")
    goal: str = Field(default="Learn LangGraph orchestration", min_length=3, max_length=1000)
    timeline_weeks: int = Field(default=8, ge=1, le=52)
    hours_per_week: int = Field(default=10, ge=1, le=80)
    max_revisions: int = Field(default=DEFAULT_MAX_REVISIONS, ge=0, le=10)
    critic_reject_until_revision: int = Field(default=0, ge=0, le=10)
    simulate_failure_node: NodeName | None = None


class GraphDemoRunResponse(BaseModel):
    final_state: dict[str, object]
    trace: list[dict[str, object]]
    warnings: list[dict[str, object]]
    errors: list[dict[str, object]]
