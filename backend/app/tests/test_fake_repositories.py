from __future__ import annotations

import pytest

from app.fixtures import canonical_demo as demo
from app.repositories.errors import DuplicateRecordError, NotFoundError
from app.repositories.fakes import (
    FakeAdaptationRepository,
    FakeAssessmentRepository,
    FakeCriticReviewRepository,
    FakeCurriculumRepository,
    FakeEvaluationRepository,
    FakeGoalRepository,
    FakeKnowledgeMapRepository,
    FakeOrchestrationRunRepository,
    FakeProgressRepository,
    FakeQuizRepository,
    FakeResourceRepository,
)
from app.schemas.enums import (
    AssessmentStatus,
    CurriculumStatus,
    GoalStatus,
    KnowledgeMapStatus,
    NodeResultStatus,
    OrchestrationRunStatus,
    ProgressStatus,
    QuizStatus,
    ResourceAttachmentStatus,
    ResourceStatus,
)
from app.schemas.orchestration import OrchestrationRunDTO, WorkflowNodeEvent


def make_run(
    status: OrchestrationRunStatus = OrchestrationRunStatus.COMPLETED,
) -> OrchestrationRunDTO:
    return OrchestrationRunDTO(
        run_id=demo.RUN_ID,
        goal_id=demo.GOAL_ID,
        workflow_version="demo-v1",
        status=status,
        current_node="complete",
        completed_nodes=[],
        failed_nodes=[],
        node_events=[],
        artifact_ids={},
        started_at=demo.NOW,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def make_node_event() -> WorkflowNodeEvent:
    return WorkflowNodeEvent(
        run_id=demo.RUN_ID,
        node_name="repository_smoke",
        status=NodeResultStatus.SUCCESS,
        message="Stored deterministic fixture",
        created_at=demo.NOW,
    )


def test_fake_repositories_store_and_query_rebuild_2_fixtures() -> None:
    goals = FakeGoalRepository()
    assessments = FakeAssessmentRepository()
    knowledge_maps = FakeKnowledgeMapRepository()
    curricula = FakeCurriculumRepository()
    resources = FakeResourceRepository()
    progress = FakeProgressRepository()
    quizzes = FakeQuizRepository()
    adaptations = FakeAdaptationRepository()
    critics = FakeCriticReviewRepository()
    evaluations = FakeEvaluationRepository()
    runs = FakeOrchestrationRunRepository()

    assert goals.create(demo.LEARNING_GOAL).goal_id == demo.GOAL_ID
    assert goals.get_by_run_id(demo.RUN_ID).goal_id == demo.GOAL_ID
    assert goals.update_status(demo.GOAL_ID, GoalStatus.ACTIVE).status is GoalStatus.ACTIVE

    assert assessments.create_session(demo.ASSESSMENT_SESSION).goal_id == demo.GOAL_ID
    for answer in demo.ASSESSMENT_ANSWERS:
        assessments.create_answer(answer)
    assert len(assessments.list_answers_by_session_id(demo.ASSESSMENT_ID)) == len(
        demo.ASSESSMENT_ANSWERS,
    )
    updated_session = assessments.update_session_status(
        demo.ASSESSMENT_ID,
        AssessmentStatus.COMPLETED,
    )
    assert updated_session.status is AssessmentStatus.COMPLETED

    assert knowledge_maps.create(demo.KNOWLEDGE_MAP).knowledge_map_id == demo.KNOWLEDGE_MAP_ID
    updated_map = knowledge_maps.update_status(demo.KNOWLEDGE_MAP_ID, KnowledgeMapStatus.ACTIVE)
    assert updated_map.status is KnowledgeMapStatus.ACTIVE

    assert curricula.create(demo.CURRICULUM).curriculum_id == demo.CURRICULUM_ID
    updated_curriculum = curricula.update_status(demo.CURRICULUM_ID, CurriculumStatus.ACTIVE)
    assert updated_curriculum.status is CurriculumStatus.ACTIVE

    for resource in demo.RESOURCE_CORPUS:
        resources.create_resource(resource)
    for attachment in demo.RESOURCE_ATTACHMENTS:
        resources.create_attachment(attachment)
    assert len(resources.list_resources()) == len(demo.RESOURCE_CORPUS)
    assert len(resources.list_attachments_by_goal_id(demo.GOAL_ID)) == len(
        demo.RESOURCE_ATTACHMENTS,
    )
    first_resource_id = demo.RESOURCE_CORPUS[0].resource_id
    first_attachment_id = demo.RESOURCE_ATTACHMENTS[0].attachment_id
    assert resources.update_resource_status(first_resource_id, ResourceStatus.ACTIVE).status
    assert resources.update_attachment_status(
        first_attachment_id,
        ResourceAttachmentStatus.ACTIVE,
    ).status

    assert progress.create(demo.PROGRESS_STATE).progress_state_id == demo.PROGRESS_ID
    updated_progress = progress.update_status(demo.PROGRESS_ID, ProgressStatus.IN_PROGRESS)
    assert updated_progress.status is ProgressStatus.IN_PROGRESS

    assert quizzes.create_quiz(demo.QUIZ).quiz_id == demo.QUIZ_ID
    assert quizzes.create_attempt(demo.QUIZ_ATTEMPT).quiz_attempt_id == demo.QUIZ_ATTEMPT_ID
    assert quizzes.update_quiz_status(demo.QUIZ_ID, QuizStatus.ACTIVE).status is QuizStatus.ACTIVE

    assert adaptations.create(demo.ADAPTATION_EVENT).adaptation_event_id == demo.ADAPTATION_ID
    assert critics.create(demo.CRITIC_REVIEW).critic_review_id == demo.CRITIC_REVIEW_ID
    assert (
        evaluations.create(demo.EVALUATION_REPORT).evaluation_report_id
        == demo.EVALUATION_REPORT_ID
    )

    run = runs.create(make_run())
    assert run.run_id == demo.RUN_ID
    assert runs.append_event(demo.RUN_ID, make_node_event()).node_events[0].node_name


def test_fake_repositories_raise_duplicate_and_not_found_errors() -> None:
    goals = FakeGoalRepository()
    goals.create(demo.LEARNING_GOAL)

    with pytest.raises(DuplicateRecordError):
        goals.create(demo.LEARNING_GOAL)

    with pytest.raises(NotFoundError):
        goals.get_by_id("goal_missing_demo")
