from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel

from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.orchestration.nodes import NODE_SEQUENCE
from app.orchestration.runner import run_straight_line_demo_from_container
from app.orchestration.state import workflow_state_to_graph_state
from app.schemas.assessment import AssessmentSessionDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.dashboard import DashboardPayload
from app.schemas.enums import OrchestrationRunStatus, OrchestrationStatus
from app.schemas.goal import LearningGoalDTO
from app.schemas.knowledge_map import KnowledgeMapDTO
from app.schemas.quiz import QuizDTO
from app.schemas.resource import ResourceDTO

ARTIFACT_TYPES = (
    AssessmentSessionDTO,
    CurriculumDTO,
    DashboardPayload,
    KnowledgeMapDTO,
    LearningGoalDTO,
    QuizDTO,
    ResourceDTO,
)


def test_straight_line_graph_completes_with_fake_backed_services() -> None:
    container = ApiServiceContainer()

    result = run_straight_line_demo_from_container(container)

    assert result.state.status == OrchestrationStatus.COMPLETED
    assert result.state.run_id == demo.RUN_ID
    assert result.state.goal_id == demo.GOAL_ID
    assert result.state.assessment_session_id == demo.ASSESSMENT_ID
    assert result.state.knowledge_map_id == demo.KNOWLEDGE_MAP_ID
    assert result.state.curriculum_id == demo.CURRICULUM_ID
    assert result.state.progress_state_id == demo.PROGRESS_ID
    assert result.state.quiz_id == demo.QUIZ_ID
    assert result.state.quiz_attempt_id == demo.QUIZ_ATTEMPT_ID
    assert result.state.adaptation_event_ids == [demo.ADAPTATION_ID]
    assert result.state.critic_review_id == demo.CRITIC_REVIEW_ID
    assert result.state.evaluation_report_id == demo.EVALUATION_REPORT_ID
    assert result.run.status == OrchestrationRunStatus.COMPLETED
    assert result.run.completed_nodes == list(NODE_SEQUENCE)
    assert result.run.failed_nodes == []

    assert container.goal_service.get_by_id(demo.GOAL_ID).goal_id == demo.GOAL_ID
    assert container.dashboard_service.get_by_run_id(demo.RUN_ID).run_summary.run_id == demo.RUN_ID
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
