from __future__ import annotations

from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo


def test_dashboard_payload_includes_frontend_safe_run_summaries() -> None:
    container = ApiServiceContainer()
    container.load_canonical_demo()

    payload = container.dashboard_service.get_by_run_id(demo.RUN_ID)

    assert payload.navigation_summary.artifact_ids["goal_id"] == demo.GOAL_ID
    assert payload.assessment_summary is not None
    assert payload.assessment_summary.assessment_session_id == demo.ASSESSMENT_ID
    assert payload.critic_summary is not None
    assert payload.critic_summary.overall_score == demo.CRITIC_REVIEW.overall_score
    assert payload.progress_summary is not None
    assert payload.progress_summary.next_action_label is not None
    assert payload.resources_summary is not None
    assert payload.resources_summary.resource_type_diversity == 0.4
    assert payload.adaptation_summary is not None
    assert payload.adaptation_summary.latest_status == demo.ADAPTATION_EVENT.status


def test_dashboard_payload_does_not_expose_quiz_answer_keys_or_raw_artifacts() -> None:
    container = ApiServiceContainer()
    container.load_canonical_demo()

    payload = container.dashboard_service.get_by_run_id(demo.RUN_ID)
    dumped = payload.model_dump_json().lower()

    assert "correct_answer" not in dumped
    assert "relevant items appearing in the top k" not in dumped
    assert "selected_options" not in dumped
    assert "question_quiz" not in dumped
    assert "traceback" not in dumped
    assert "secret" not in dumped
