from __future__ import annotations

from app.api.v1.dependencies import ApiServiceContainer
from app.orchestration.runner import run_straight_line_demo_from_container
from app.schemas.enums import NodeResultStatus


def test_curriculum_resource_and_critic_events_are_safe() -> None:
    result = run_straight_line_demo_from_container(ApiServiceContainer())
    messages = [
        event.message
        for event in result.run.node_events
        if event.message
    ]

    assert "agent=curriculum artifact_id=curriculum_demo_rag_v1" in messages
    assert "agent=resource artifact_id=resource_attachments" in messages
    assert "agent=critic artifact_id=critic_demo_rag" in messages
    for event in result.run.node_events:
        assert event.status == NodeResultStatus.SUCCESS
    for message in messages:
        dumped = message.lower()
        assert "prompt" not in dumped
        assert "payload" not in dumped
        assert "traceback" not in dumped
        assert "secret" not in dumped
        assert "resource_rag_intro" not in dumped
