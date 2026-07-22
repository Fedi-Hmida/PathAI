from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel

from app.agents.mock import MockQuizAgent
from app.agents.services import build_mock_agent_service_bundle
from app.agents.services.quiz import QuizAgentService
from app.api.v1.dependencies import ApiServiceContainer
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo, run_straight_line_demo_from_container
from app.orchestration.state import workflow_state_to_graph_state
from app.schemas.adaptation import AdaptationEventDTO
from app.schemas.enums import AdaptationStatus, OrchestrationRunStatus, OrchestrationStatus
from app.schemas.progress import ProgressStateDTO
from app.schemas.quiz import QuizAttemptDTO, QuizDTO

ARTIFACT_TYPES = (
    AdaptationEventDTO,
    ProgressStateDTO,
    QuizAttemptDTO,
    QuizDTO,
)


def test_orchestration_runs_progress_quiz_and_adaptation_behavior() -> None:
    container = ApiServiceContainer()

    result = run_straight_line_demo_from_container(container)

    curriculum = container.curriculum_service.get_by_id(result.state.curriculum_id or "")
    progress = container.progress_service.get_by_id(result.state.progress_state_id or "")
    quiz = container.quiz_service.get_quiz_by_id(result.state.quiz_id or "")
    attempt = container.quiz_service.get_attempt_by_id(result.state.quiz_attempt_id or "")
    adaptation = container.adaptation_service.get_by_id(result.state.adaptation_event_ids[-1])

    assert result.state.status == OrchestrationStatus.COMPLETED
    assert result.run.status == OrchestrationRunStatus.COMPLETED
    assert len(progress.topic_progress) == sum(len(week.topics) for week in curriculum.weeks)
    assert {
        "retrieval_evaluation",
        "vector_search",
        "chunking",
    } <= set(quiz.target_concept_ids)
    assert attempt.total_score < 0.65
    assert attempt.adaptation_triggered is True
    assert result.state.quiz_score == attempt.total_score
    assert adaptation.status == AdaptationStatus.PROPOSED
    assert adaptation.new_curriculum_id is None
    assert not _contains_artifact_dto(workflow_state_to_graph_state(result.state))


def test_quiz_agent_validation_failure_marks_workflow_failed_safely() -> None:
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
    agents.quiz = QuizAgentService(MockQuizAgent(malformed=True), container.quiz_service)

    result = run_straight_line_demo(
        OrchestrationContext.from_container(container, agent_services=agents),
    )

    assert result.state.status == OrchestrationStatus.FAILED
    assert result.state.current_node == "load_quiz"
    assert result.run.status == OrchestrationRunStatus.FAILED
    assert result.run.failed_nodes == ["load_quiz"]
    failed_event = result.run.node_events[-1]
    assert failed_event.message == "agent=quiz status=failed"
    dumped = failed_event.model_dump_json().lower()
    assert "invalid" not in dumped
    assert "payload" not in dumped
    assert "correct_answer" not in dumped


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
