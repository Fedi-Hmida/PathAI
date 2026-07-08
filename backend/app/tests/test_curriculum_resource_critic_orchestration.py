from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel

from app.agents.mock import MockCriticAgent
from app.agents.services import build_mock_agent_service_bundle
from app.agents.services.critic import CriticAgentService
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo, run_straight_line_demo_from_container
from app.orchestration.state import workflow_state_to_graph_state
from app.schemas.critic import CriticReviewDTO
from app.schemas.curriculum import CurriculumDTO
from app.schemas.dashboard import DashboardPayload
from app.schemas.enums import OrchestrationRunStatus, OrchestrationStatus
from app.schemas.resource import ResourceAttachmentDTO, ResourceDTO

FORBIDDEN_STATE_TYPES = (
    CurriculumDTO,
    ResourceAttachmentDTO,
    ResourceDTO,
    CriticReviewDTO,
    DashboardPayload,
)


def test_orchestration_deepens_curriculum_resource_and_critic_steps() -> None:
    container = ApiServiceContainer()

    result = run_straight_line_demo_from_container(container)

    curriculum = container.curriculum_service.get_by_id(demo.CURRICULUM_ID)
    attachments = container.resource_service.list_attachments_by_curriculum_id(
        demo.CURRICULUM_ID,
    )
    critic = container.critic_service.get_by_id(demo.CRITIC_REVIEW_ID)
    topic_concepts = {
        concept
        for week in curriculum.weeks
        for topic in week.topics
        for concept in topic.concept_ids
    }

    assert result.state.status == OrchestrationStatus.COMPLETED
    assert result.state.curriculum_id == demo.CURRICULUM_ID
    assert result.state.critic_review_id == demo.CRITIC_REVIEW_ID
    assert {"retrieval_evaluation", "vector_search", "reranking"} <= topic_concepts
    assert len(attachments) >= len([topic for week in curriculum.weeks for topic in week.topics])
    assert critic.overall_score >= 0.85
    assert critic.issues == []
    assert not _contains_forbidden_state_type(workflow_state_to_graph_state(result.state))


def test_controlled_critic_failure_marks_workflow_failed_safely() -> None:
    container = ApiServiceContainer()
    agents = build_mock_agent_service_bundle(
        assessments=container.assessment_service,
        knowledge_maps=container.knowledge_map_service,
        curricula=container.curriculum_service,
        resources=container.resource_service,
        critics=container.critic_service,
        progress=container.progress_service,
        quizzes=container.quiz_service,
        adaptations=container.adaptation_service,
        evaluations=container.evaluation_service,
    )
    agents.critic = CriticAgentService(
        MockCriticAgent(malformed=True),
        container.critic_service,
    )

    result = run_straight_line_demo(
        OrchestrationContext.from_container(container, agent_services=agents),
    )

    assert result.state.status == OrchestrationStatus.FAILED
    assert result.state.current_node == "load_critic_review"
    assert result.run.status == OrchestrationRunStatus.FAILED
    failed_event = result.run.node_events[-1]
    assert failed_event.message == "agent=critic status=failed"
    dumped = failed_event.model_dump_json().lower()
    assert "invalid" not in dumped
    assert "payload" not in dumped
    assert "traceback" not in dumped


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
