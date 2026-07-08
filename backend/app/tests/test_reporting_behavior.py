from __future__ import annotations

from app.api.v1.dependencies import ApiServiceContainer
from app.fixtures import canonical_demo as demo
from app.schemas.reporting import ReportingSummaryDTO


def test_reporting_summary_packages_demo_readiness_from_dashboard_payload() -> None:
    container = ApiServiceContainer()
    container.load_canonical_demo()

    summary = container.reporting_service.get_summary_by_run_id(demo.RUN_ID)

    assert ReportingSummaryDTO.model_validate(summary) == summary
    assert summary.run_id == demo.RUN_ID
    assert summary.goal_id == demo.GOAL_ID
    assert summary.deterministic is True
    assert summary.demo_ready is True
    assert summary.artifact_ids["evaluation_report_id"] == demo.EVALUATION_REPORT_ID
    assert summary.overall_quality_score == demo.EVALUATION_REPORT.overall_score
    assert "retrieval_evaluation" in summary.weak_concepts
    assert summary.next_action is not None
    assert summary.readiness_notes


def test_reporting_summary_is_compact_and_answer_key_safe() -> None:
    container = ApiServiceContainer()
    container.load_canonical_demo()

    dumped = (
        container.reporting_service.get_summary_by_run_id(demo.RUN_ID)
        .model_dump_json()
        .lower()
    )

    assert "correct_answer" not in dumped
    assert "question_quiz" not in dumped
    assert "selected_options" not in dumped
    assert "prompt" not in dumped
    assert "traceback" not in dumped
