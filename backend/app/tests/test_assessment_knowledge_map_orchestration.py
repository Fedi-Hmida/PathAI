from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel

from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.orchestration.runner import run_straight_line_demo_from_container
from app.orchestration.state import workflow_state_to_graph_state
from app.schemas.assessment import AssessmentAnswerDTO, AssessmentSessionDTO
from app.schemas.dashboard import DashboardPayload
from app.schemas.enums import OrchestrationStatus
from app.schemas.knowledge_map import KnowledgeMapDTO

FORBIDDEN_STATE_TYPES = (
    AssessmentAnswerDTO,
    AssessmentSessionDTO,
    DashboardPayload,
    KnowledgeMapDTO,
)


def test_orchestration_uses_agent_backed_assessment_and_knowledge_map() -> None:
    container = ApiServiceContainer()

    result = run_straight_line_demo_from_container(container)

    assert result.state.status == OrchestrationStatus.COMPLETED
    assert result.state.assessment_session_id == demo.ASSESSMENT_ID
    assert result.state.assessment_question_count == len(demo.ASSESSMENT_QUESTIONS)
    assert result.state.assessment_confidence >= 0.75
    assert result.state.knowledge_map_id == demo.KNOWLEDGE_MAP_ID

    assessment = container.assessment_service.get_session_by_id(demo.ASSESSMENT_ID)
    knowledge_map = container.knowledge_map_service.get_by_id(demo.KNOWLEDGE_MAP_ID)
    assert len(assessment.concept_evidence) >= 6
    assert "retrieval_evaluation" in knowledge_map.weak_concepts
    assert "production_rag_failures" in knowledge_map.missing_concepts
    assert not _contains_forbidden_state_type(workflow_state_to_graph_state(result.state))


def _contains_forbidden_state_type(value: Any) -> bool:
    if isinstance(value, FORBIDDEN_STATE_TYPES):
        return True
    if isinstance(value, BaseModel):
        return False
    if isinstance(value, dict):
        return any(_contains_forbidden_state_type(item) for item in value.values())
    if isinstance(value, Iterable) and not isinstance(value, str):
        return any(_contains_forbidden_state_type(item) for item in value)
    return False
