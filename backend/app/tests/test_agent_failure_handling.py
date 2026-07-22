from __future__ import annotations

from app.agents.mock import MockKnowledgeMapAgent
from app.agents.services import build_mock_agent_service_bundle
from app.agents.services.knowledge_map import KnowledgeMapAgentService
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo
from app.schemas.enums import NodeResultStatus, OrchestrationRunStatus, OrchestrationStatus


def test_controlled_agent_failure_marks_workflow_failed_safely() -> None:
    container = ApiServiceContainer()
    agents = build_mock_agent_service_bundle(
        goals=container.goal_service,
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
    agents.knowledge_map = KnowledgeMapAgentService(
        MockKnowledgeMapAgent(malformed=True),
        container.knowledge_map_service,
    )

    result = run_straight_line_demo(
        OrchestrationContext.from_container(container, agent_services=agents),
    )

    assert result.state.status == OrchestrationStatus.FAILED
    assert result.state.current_node == "load_knowledge_map"
    assert result.run.status == OrchestrationRunStatus.FAILED
    assert result.run.failed_nodes == ["load_knowledge_map"]
    failed_event = result.run.node_events[-1]
    assert failed_event.status == NodeResultStatus.FAILED
    assert failed_event.message == "agent=knowledge_map status=failed"
    assert failed_event.errors[0].category == "agent"
    assert failed_event.errors[0].metadata == {"agent_name": "knowledge_map"}
    dumped = failed_event.model_dump_json().lower()
    assert "invalid" not in dumped
    assert "payload" not in dumped
    assert container.orchestration_run_service.get_by_id(demo.RUN_ID).status == (
        OrchestrationRunStatus.FAILED
    )
