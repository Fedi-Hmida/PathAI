from __future__ import annotations

from app.agents.mock import MockKnowledgeMapAgent
from app.agents.services.knowledge_map import KnowledgeMapAgentService
from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.orchestration.nodes import NODE_SEQUENCE, OrchestrationContext
from app.orchestration.runner import run_straight_line_demo
from app.schemas.enums import NodeResultStatus, OrchestrationRunStatus, OrchestrationStatus


def test_successful_graph_records_node_events_in_order() -> None:
    container = ApiServiceContainer()

    result = run_straight_line_demo(
        OrchestrationContext.from_container(container),
    )

    events = result.run.node_events
    assert [event.node_name for event in events] == list(NODE_SEQUENCE)
    assert {event.status for event in events} == {NodeResultStatus.SUCCESS}


def test_controlled_node_failure_marks_failed_status_and_records_safe_event() -> None:
    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)
    context.agent_services.knowledge_map = KnowledgeMapAgentService(
        MockKnowledgeMapAgent(fail=True),
        container.knowledge_map_service,
    )

    result = run_straight_line_demo(context)

    assert result.state.status == OrchestrationStatus.FAILED
    assert result.state.current_node == "load_knowledge_map"
    assert result.run.status == OrchestrationRunStatus.FAILED
    assert result.run.completed_nodes == ["initialize_run", "load_goal", "load_assessment"]
    assert result.run.failed_nodes == ["load_knowledge_map"]
    assert [event.node_name for event in result.run.node_events] == [
        "initialize_run",
        "load_goal",
        "load_assessment",
        "load_knowledge_map",
    ]
    failed_event = result.run.node_events[-1]
    assert failed_event.status == NodeResultStatus.FAILED
    assert failed_event.errors
    assert failed_event.errors[0].message == "Agent step failed: knowledge_map"
    assert failed_event.message == "agent=knowledge_map status=failed"
    assert "agent execution failed" not in failed_event.model_dump_json()
    assert container.orchestration_run_service.get_by_id(demo.RUN_ID).status == (
        OrchestrationRunStatus.FAILED
    )
