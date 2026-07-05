from __future__ import annotations

from app.fixtures import canonical_demo as demo
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
from app.repositories.protocols import (
    AdaptationRepository,
    AssessmentRepository,
    CriticReviewRepository,
    CurriculumRepository,
    EvaluationRepository,
    GoalRepository,
    KnowledgeMapRepository,
    OrchestrationRunRepository,
    ProgressRepository,
    QuizRepository,
    ResourceRepository,
)
from app.schemas.enums import OrchestrationRunStatus
from app.schemas.orchestration import OrchestrationRunDTO
from app.services import (
    AdaptationService,
    AssessmentService,
    CriticService,
    CurriculumService,
    EvaluationService,
    GoalService,
    KnowledgeMapService,
    OrchestrationRunService,
    ProgressService,
    QuizService,
    ResourceService,
)


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


def test_service_skeletons_delegate_to_fake_repositories() -> None:
    goal_repository: GoalRepository = FakeGoalRepository()
    assessment_repository: AssessmentRepository = FakeAssessmentRepository()
    knowledge_map_repository: KnowledgeMapRepository = FakeKnowledgeMapRepository()
    curriculum_repository: CurriculumRepository = FakeCurriculumRepository()
    resource_repository: ResourceRepository = FakeResourceRepository()
    progress_repository: ProgressRepository = FakeProgressRepository()
    quiz_repository: QuizRepository = FakeQuizRepository()
    adaptation_repository: AdaptationRepository = FakeAdaptationRepository()
    critic_repository: CriticReviewRepository = FakeCriticReviewRepository()
    evaluation_repository: EvaluationRepository = FakeEvaluationRepository()
    run_repository: OrchestrationRunRepository = FakeOrchestrationRunRepository()

    assert GoalService(goal_repository).create(demo.LEARNING_GOAL).goal_id == demo.GOAL_ID
    assert AssessmentService(assessment_repository).create_session(
        demo.ASSESSMENT_SESSION,
    ).assessment_session_id == demo.ASSESSMENT_ID
    assert KnowledgeMapService(knowledge_map_repository).create(
        demo.KNOWLEDGE_MAP,
    ).knowledge_map_id == demo.KNOWLEDGE_MAP_ID
    assert CurriculumService(curriculum_repository).create(
        demo.CURRICULUM,
    ).curriculum_id == demo.CURRICULUM_ID
    assert ResourceService(resource_repository).create_resource(
        demo.RESOURCE_CORPUS[0],
    ).resource_id == demo.RESOURCE_CORPUS[0].resource_id
    assert ProgressService(progress_repository).create(
        demo.PROGRESS_STATE,
    ).progress_state_id == demo.PROGRESS_ID
    assert QuizService(quiz_repository).create_quiz(demo.QUIZ).quiz_id == demo.QUIZ_ID
    assert AdaptationService(adaptation_repository).create(
        demo.ADAPTATION_EVENT,
    ).adaptation_event_id == demo.ADAPTATION_ID
    assert CriticService(critic_repository).create(
        demo.CRITIC_REVIEW,
    ).critic_review_id == demo.CRITIC_REVIEW_ID
    assert EvaluationService(evaluation_repository).create(
        demo.EVALUATION_REPORT,
    ).evaluation_report_id == demo.EVALUATION_REPORT_ID
    assert OrchestrationRunService(run_repository).create(make_run()).run_id == demo.RUN_ID
