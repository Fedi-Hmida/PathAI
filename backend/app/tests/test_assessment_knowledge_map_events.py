from __future__ import annotations

from app.api.v1.dependencies import ApiServiceContainer
from app.orchestration.runner import run_straight_line_demo_from_container
from app.schemas.enums import NodeResultStatus


def test_assessment_and_knowledge_map_events_are_safe() -> None:
    result = run_straight_line_demo_from_container(ApiServiceContainer())

    messages = [
        event.message
        for event in result.run.node_events
        if event.message
    ]

    assert "agent=assessment artifact_id=assessment_demo_rag" in messages
    assert "agent=knowledge_map artifact_id=kmap_demo_rag" in messages
    for event in result.run.node_events:
        assert event.status == NodeResultStatus.SUCCESS
    for message in messages:
        dumped = message.lower()
        assert "prompt" not in dumped
        assert "payload" not in dumped
        assert "traceback" not in dumped
        assert "secret" not in dumped
