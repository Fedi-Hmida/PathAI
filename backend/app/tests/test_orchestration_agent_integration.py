from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel

from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.orchestration.runner import run_straight_line_demo_from_container
from app.orchestration.state import workflow_state_to_graph_state
from app.schemas.assessment import AssessmentSessionDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.dashboard import DashboardPayload
from app.schemas.enums import OrchestrationStatus
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.schemas.quiz import QuizDTO
from app.schemas.resource import ResourceDTO

ARTIFACT_TYPES = (
    AssessmentSessionDTO,
    CurriculumDTO,
    DashboardPayload,
    KnowledgeMapDTO,
    QuizDTO,
    ResourceDTO,
)


def test_orchestration_runs_through_agent_services() -> None:
    container = ApiServiceContainer()

    result = run_straight_line_demo_from_container(container)

    assert result.state.status == OrchestrationStatus.COMPLETED
    assert result.state.knowledge_map_id == demo.KNOWLEDGE_MAP_ID
    assert result.state.curriculum_id == demo.CURRICULUM_ID
    assert result.state.quiz_attempt_id == demo.QUIZ_ATTEMPT_ID
    assert result.run.artifact_ids["evaluation_report_id"] == demo.EVALUATION_REPORT_ID

    event_messages = [event.message for event in result.run.node_events if event.message]
    assert "agent=assessment artifact_id=assessment_demo_rag" in event_messages
    assert "agent=knowledge_map artifact_id=kmap_demo_rag" in event_messages
    assert "agent=evaluation artifact_id=eval_demo_rag" in event_messages
    assert not _contains_artifact_dto(workflow_state_to_graph_state(result.state))


def _contains_artifact_dto(value: Any) -> bool:
    if isinstance(value, ARTIFACT_TYPES):
        return True
    if isinstance(value, BaseModel):
        return False
    if isinstance(value, dict):
        return any(_contains_artifact_dto(item) for item in value.values())
    if isinstance(value, Iterable) and not isinstance(value, str):
        return any(_contains_artifact_dto(item) for item in value)
    return False
