from __future__ import annotations

from app.api.v1.dependencies import ApiServiceContainer
from app.orchestration.runner import run_straight_line_demo_from_container


def test_evaluation_dashboard_reporting_events_are_safe_and_ordered() -> None:
    container = ApiServiceContainer()

    result = run_straight_line_demo_from_container(container)

    messages = [event.message for event in result.run.node_events if event.message]
    node_names = [event.node_name for event in result.run.node_events]
    evaluation_index = node_names.index("load_evaluation")
    dashboard_index = node_names.index("prepare_dashboard_payload")

    assert "agent=evaluation artifact_id=eval_demo_rag" in messages
    assert evaluation_index < dashboard_index
    for message in messages:
        normalized = message.lower()
        assert "correct_answer" not in normalized
        assert "selected_options" not in normalized
        assert "dashboardpayload" not in normalized
        assert "reportingsummary" not in normalized
        assert "traceback" not in normalized
        assert "secret" not in normalized


def test_evaluation_dashboard_reporting_events_do_not_store_payload_bodies() -> None:
    container = ApiServiceContainer()

    result = run_straight_line_demo_from_container(container)

    for event in result.run.node_events:
        dumped = event.model_dump_json().lower()
        assert "resource diversity score" not in dumped
        assert "latest quiz score" not in dumped
        assert "correct_answer" not in dumped
        assert "question_quiz" not in dumped
