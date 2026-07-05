from __future__ import annotations

from app.api.v1.dependencies import ApiServiceContainer
from app.orchestration.runner import run_straight_line_demo_from_container
from app.schemas.enums import NodeResultStatus


def test_agent_node_events_include_safe_agent_metadata() -> None:
    result = run_straight_line_demo_from_container(ApiServiceContainer())

    agent_events = [event for event in result.run.node_events if event.message]

    assert agent_events
    assert all(event.status == NodeResultStatus.SUCCESS for event in agent_events)
    assert any(event.message == "agent=quiz artifact_id=quiz_demo_rag" for event in agent_events)
    assert all("payload" not in event.model_dump_json().lower() for event in agent_events)
    assert all("traceback" not in event.model_dump_json().lower() for event in agent_events)
