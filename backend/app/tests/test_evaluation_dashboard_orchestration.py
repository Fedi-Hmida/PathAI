from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel

from app.agents.mock import MockEvaluationAgent
from app.agents.services import build_mock_agent_service_bundle
from app.agents.services.evaluation import EvaluationAgentService
from app.api.v1.dependencies import ApiServiceContainer
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo, run_straight_line_demo_from_container
from app.orchestration.state import workflow_state_to_graph_state
from app.schemas.dashboard import DashboardPayload
from app.schemas.enums import OrchestrationRunStatus, OrchestrationStatus
from app.schemas.evaluation import EvaluationReportDTO
from app.schemas.reporting import ReportingSummaryDTO

ARTIFACT_TYPES = (
    DashboardPayload,
    EvaluationReportDTO,
    ReportingSummaryDTO,
)


def test_orchestration_generates_evaluation_dashboard_and_reporting_summary() -> None:
    container = ApiServiceContainer()

    result = run_straight_line_demo_from_container(container)
    report = container.evaluation_service.get_by_id(result.state.evaluation_report_id or "")
    dashboard = container.dashboard_service.get_by_run_id(result.state.run_id)
    reporting = container.reporting_service.get_summary_by_run_id(result.state.run_id)

    assert result.state.status == OrchestrationStatus.COMPLETED
    assert result.run.status == OrchestrationRunStatus.COMPLETED
    assert report.overall_score >= 0.7
    assert dashboard.evaluation_summary is not None
    assert reporting.demo_ready is True
    assert result.state.evaluation_report_id == report.evaluation_report_id
    assert not _contains_artifact_dto(workflow_state_to_graph_state(result.state))


def test_evaluation_validation_failure_marks_workflow_failed_safely() -> None:
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
    agents.evaluation = EvaluationAgentService(
        MockEvaluationAgent(malformed=True),
        container.evaluation_service,
    )

    result = run_straight_line_demo(
        OrchestrationContext.from_container(container, agent_services=agents),
    )

    assert result.state.status == OrchestrationStatus.FAILED
    assert result.state.current_node == "load_evaluation"
    assert result.run.status == OrchestrationRunStatus.FAILED
    assert result.run.failed_nodes == ["load_evaluation"]
    failed_event = result.run.node_events[-1]
    assert failed_event.message == "agent=evaluation status=failed"
    dumped = failed_event.model_dump_json().lower()
    assert "invalid" not in dumped
    assert "payload" not in dumped
    assert "traceback" not in dumped


def _contains_artifact_dto(value: Any) -> bool:
    if isinstance(value, ARTIFACT_TYPES):
        return True
    if isinstance(value, BaseModel):
        return False
    if isinstance(value, dict):
        return any(_contains_artifact_dto(item) for item in value.values())
    if isinstance(value, Iterable) and not isinstance(value, str):
        return any(_contains_artifact_dto(item) for item in value)
    return False
