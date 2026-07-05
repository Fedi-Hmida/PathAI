from __future__ import annotations

from app.fixtures import canonical_demo as demo
from app.repositories.fakes import (
    FakeAdaptationRepository,
    FakeCurriculumRepository,
    FakeEvaluationRepository,
    FakeGoalRepository,
    FakeKnowledgeMapRepository,
    FakeOrchestrationRunRepository,
    FakeProgressRepository,
    FakeQuizRepository,
    FakeResourceRepository,
)
from app.schemas.enums import OrchestrationRunStatus
from app.schemas.orchestration import OrchestrationRunDTO
from app.services.dashboard import DashboardService


def make_run() -> OrchestrationRunDTO:
    return OrchestrationRunDTO(
        run_id=demo.RUN_ID,
        goal_id=demo.GOAL_ID,
        workflow_version="demo-v1",
        status=OrchestrationRunStatus.COMPLETED,
        current_node="complete",
        completed_nodes=[],
        failed_nodes=[],
        node_events=[],
        artifact_ids={},
        started_at=demo.NOW,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def test_dashboard_service_composes_read_only_payload_from_repositories() -> None:
    goals = FakeGoalRepository()
    runs = FakeOrchestrationRunRepository()
    knowledge_maps = FakeKnowledgeMapRepository()
    curricula = FakeCurriculumRepository()
    resources = FakeResourceRepository()
    progress_states = FakeProgressRepository()
    quizzes = FakeQuizRepository()
    adaptations = FakeAdaptationRepository()
    evaluations = FakeEvaluationRepository()

    goals.create(demo.LEARNING_GOAL)
    runs.create(make_run())
    knowledge_maps.create(demo.KNOWLEDGE_MAP)
    curricula.create(demo.CURRICULUM)
    progress_states.create(demo.PROGRESS_STATE)
    quizzes.create_quiz(demo.QUIZ)
    quizzes.create_attempt(demo.QUIZ_ATTEMPT)
    adaptations.create(demo.ADAPTATION_EVENT)
    evaluations.create(demo.EVALUATION_REPORT)
    for resource in demo.RESOURCE_CORPUS:
        resources.create_resource(resource)
    for attachment in demo.RESOURCE_ATTACHMENTS:
        resources.create_attachment(attachment)

    payload = DashboardService(
        goals=goals,
        orchestration_runs=runs,
        knowledge_maps=knowledge_maps,
        curricula=curricula,
        resources=resources,
        progress_states=progress_states,
        quizzes=quizzes,
        adaptations=adaptations,
        evaluations=evaluations,
    ).get_by_run_id(demo.RUN_ID)

    assert payload.run_summary.run_id == demo.RUN_ID
    assert payload.goal_summary.goal_id == demo.GOAL_ID
    assert payload.knowledge_map_summary is not None
    assert payload.curriculum_summary is not None
    assert payload.progress_summary is not None
    assert payload.quiz_summary is not None
    assert payload.resources_summary is not None
    assert payload.resources_summary.total_attached == len(demo.RESOURCE_ATTACHMENTS)
    assert payload.adaptation_summary is not None
    assert payload.evaluation_summary is not None
    assert payload.ui_flags.show_adaptation_alert is True

    payload.goal_summary.text = "Mutated dashboard response"

    assert goals.get_by_id(demo.GOAL_ID).goal_text == demo.LEARNING_GOAL.goal_text
