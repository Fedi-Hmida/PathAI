from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel

from app.fixtures import canonical_demo as demo
from app.orchestration.state import (
    build_initial_workflow_state,
    graph_state_to_workflow_state,
    workflow_state_to_graph_state,
)
from app.schemas.assessment import AssessmentSessionDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.dashboard import DashboardPayload
from app.schemas.enums import ExecutionMode, OrchestrationStatus
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


def test_initial_workflow_state_is_lightweight_and_round_trips() -> None:
    state = build_initial_workflow_state(
        run_id=demo.RUN_ID,
        goal_id=demo.GOAL_ID,
        mode=ExecutionMode.DEMO,
        created_at=demo.NOW,
    )

    assert state.run_id == demo.RUN_ID
    assert state.goal_id == demo.GOAL_ID
    assert state.status == OrchestrationStatus.QUEUED
    assert state.mode == ExecutionMode.DEMO
    assert state.current_node is None
    assert state.trace_metadata.run_id == demo.RUN_ID

    graph_state = workflow_state_to_graph_state(state)
    round_tripped = graph_state_to_workflow_state(graph_state)

    assert round_tripped == state
    assert not _contains_artifact_dto(graph_state)


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
