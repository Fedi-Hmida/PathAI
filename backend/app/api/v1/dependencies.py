from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import Depends

from app.api.v1.responses import DemoLoadFixturesResponse
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
from app.schemas.enums import (
    DifficultyLevel,
    ExecutionMode,
    GoalStatus,
    OrchestrationRunStatus,
)
from app.schemas.goal import LearnerProfile, LearningGoalCreate, LearningGoalDTO
from app.schemas.orchestration import OrchestrationRunDTO
from app.services import (
    AdaptationService,
    AssessmentService,
    CriticService,
    CurriculumService,
    DashboardService,
    EvaluationService,
    GoalService,
    KnowledgeMapService,
    OrchestrationRunService,
    ProgressService,
    QuizService,
    ReportingService,
    ResourceService,
)


@dataclass(slots=True)
class ApiServiceContainer:
    goal_repository: FakeGoalRepository = field(default_factory=FakeGoalRepository)
    assessment_repository: FakeAssessmentRepository = field(
        default_factory=FakeAssessmentRepository,
    )
    knowledge_map_repository: FakeKnowledgeMapRepository = field(
        default_factory=FakeKnowledgeMapRepository,
    )
    curriculum_repository: FakeCurriculumRepository = field(
        default_factory=FakeCurriculumRepository,
    )
    resource_repository: FakeResourceRepository = field(default_factory=FakeResourceRepository)
    progress_repository: FakeProgressRepository = field(default_factory=FakeProgressRepository)
    quiz_repository: FakeQuizRepository = field(default_factory=FakeQuizRepository)
    adaptation_repository: FakeAdaptationRepository = field(
        default_factory=FakeAdaptationRepository,
    )
    critic_repository: FakeCriticReviewRepository = field(
        default_factory=FakeCriticReviewRepository,
    )
    evaluation_repository: FakeEvaluationRepository = field(
        default_factory=FakeEvaluationRepository,
    )
    orchestration_run_repository: FakeOrchestrationRunRepository = field(
        default_factory=FakeOrchestrationRunRepository,
    )
    goal_service: GoalService = field(init=False)
    assessment_service: AssessmentService = field(init=False)
    knowledge_map_service: KnowledgeMapService = field(init=False)
    curriculum_service: CurriculumService = field(init=False)
    resource_service: ResourceService = field(init=False)
    progress_service: ProgressService = field(init=False)
    quiz_service: QuizService = field(init=False)
    adaptation_service: AdaptationService = field(init=False)
    critic_service: CriticService = field(init=False)
    evaluation_service: EvaluationService = field(init=False)
    orchestration_run_service: OrchestrationRunService = field(init=False)
    dashboard_service: DashboardService = field(init=False)
    reporting_service: ReportingService = field(init=False)

    def __post_init__(self) -> None:
        self.goal_service = GoalService(self.goal_repository)
        self.assessment_service = AssessmentService(self.assessment_repository)
        self.knowledge_map_service = KnowledgeMapService(self.knowledge_map_repository)
        self.curriculum_service = CurriculumService(self.curriculum_repository)
        self.resource_service = ResourceService(self.resource_repository)
        self.progress_service = ProgressService(self.progress_repository)
        self.quiz_service = QuizService(self.quiz_repository)
        self.adaptation_service = AdaptationService(self.adaptation_repository)
        self.critic_service = CriticService(self.critic_repository)
        self.evaluation_service = EvaluationService(self.evaluation_repository)
        self.orchestration_run_service = OrchestrationRunService(
            self.orchestration_run_repository,
        )
        self.dashboard_service = DashboardService(
            goals=self.goal_repository,
            orchestration_runs=self.orchestration_run_repository,
            knowledge_maps=self.knowledge_map_repository,
            curricula=self.curriculum_repository,
            resources=self.resource_repository,
            progress_states=self.progress_repository,
            quizzes=self.quiz_repository,
            adaptations=self.adaptation_repository,
            evaluations=self.evaluation_repository,
            assessments=self.assessment_repository,
            critics=self.critic_repository,
        )
        self.reporting_service = ReportingService(self.dashboard_service)

    def clear(self) -> None:
        self.goal_repository.clear()
        self.assessment_repository.clear()
        self.knowledge_map_repository.clear()
        self.curriculum_repository.clear()
        self.resource_repository.clear()
        self.progress_repository.clear()
        self.quiz_repository.clear()
        self.adaptation_repository.clear()
        self.critic_repository.clear()
        self.evaluation_repository.clear()
        self.orchestration_run_repository.clear()

    def load_canonical_demo(self) -> DemoLoadFixturesResponse:
        self.clear()
        self.goal_service.create(demo.LEARNING_GOAL)
        self.orchestration_run_service.create(_canonical_orchestration_run())
        self.assessment_service.create_session(demo.ASSESSMENT_SESSION)
        for answer in demo.ASSESSMENT_ANSWERS:
            self.assessment_service.create_answer(answer)
        self.knowledge_map_service.create(demo.KNOWLEDGE_MAP)
        self.curriculum_service.create(demo.CURRICULUM)
        for resource in demo.RESOURCE_CORPUS:
            self.resource_service.create_resource(resource)
        for attachment in demo.RESOURCE_ATTACHMENTS:
            self.resource_service.create_attachment(attachment)
        self.progress_service.create(demo.PROGRESS_STATE)
        self.quiz_service.create_quiz(demo.QUIZ)
        self.quiz_service.create_attempt(demo.QUIZ_ATTEMPT)
        self.adaptation_service.create(demo.ADAPTATION_EVENT)
        self.critic_service.create(demo.CRITIC_REVIEW)
        self.evaluation_service.create(demo.EVALUATION_REPORT)

        return DemoLoadFixturesResponse(
            message="deterministic local demo fixtures loaded",
            mode=ExecutionMode.DEMO,
            deterministic=True,
            run_id=demo.RUN_ID,
            goal_id=demo.GOAL_ID,
            assessment_id=demo.ASSESSMENT_ID,
            knowledge_map_id=demo.KNOWLEDGE_MAP_ID,
            curriculum_id=demo.CURRICULUM_ID,
            progress_id=demo.PROGRESS_ID,
            quiz_id=demo.QUIZ_ID,
            quiz_attempt_id=demo.QUIZ_ATTEMPT_ID,
            adaptation_id=demo.ADAPTATION_ID,
            critic_id=demo.CRITIC_REVIEW_ID,
            evaluation_id=demo.EVALUATION_REPORT_ID,
            dashboard_payload=self.dashboard_service.get_by_run_id(demo.RUN_ID),
        )


_api_container = ApiServiceContainer()


def get_api_container() -> ApiServiceContainer:
    return _api_container


ApiContainerDependency = Annotated[ApiServiceContainer, Depends(get_api_container)]


def get_goal_service(container: ApiContainerDependency) -> GoalService:
    return container.goal_service


def get_assessment_service(container: ApiContainerDependency) -> AssessmentService:
    return container.assessment_service


def get_knowledge_map_service(container: ApiContainerDependency) -> KnowledgeMapService:
    return container.knowledge_map_service


def get_curriculum_service(container: ApiContainerDependency) -> CurriculumService:
    return container.curriculum_service


def get_resource_service(container: ApiContainerDependency) -> ResourceService:
    return container.resource_service


def get_progress_service(container: ApiContainerDependency) -> ProgressService:
    return container.progress_service


def get_quiz_service(container: ApiContainerDependency) -> QuizService:
    return container.quiz_service


def get_adaptation_service(container: ApiContainerDependency) -> AdaptationService:
    return container.adaptation_service


def get_critic_service(container: ApiContainerDependency) -> CriticService:
    return container.critic_service


def get_evaluation_service(container: ApiContainerDependency) -> EvaluationService:
    return container.evaluation_service


def get_orchestration_run_service(
    container: ApiContainerDependency,
) -> OrchestrationRunService:
    return container.orchestration_run_service


def get_dashboard_service(container: ApiContainerDependency) -> DashboardService:
    return container.dashboard_service


GoalServiceDependency = Annotated[GoalService, Depends(get_goal_service)]
AssessmentServiceDependency = Annotated[AssessmentService, Depends(get_assessment_service)]
KnowledgeMapServiceDependency = Annotated[
    KnowledgeMapService,
    Depends(get_knowledge_map_service),
]
CurriculumServiceDependency = Annotated[CurriculumService, Depends(get_curriculum_service)]
ResourceServiceDependency = Annotated[ResourceService, Depends(get_resource_service)]
ProgressServiceDependency = Annotated[ProgressService, Depends(get_progress_service)]
QuizServiceDependency = Annotated[QuizService, Depends(get_quiz_service)]
AdaptationServiceDependency = Annotated[AdaptationService, Depends(get_adaptation_service)]
CriticServiceDependency = Annotated[CriticService, Depends(get_critic_service)]
EvaluationServiceDependency = Annotated[EvaluationService, Depends(get_evaluation_service)]
OrchestrationRunServiceDependency = Annotated[
    OrchestrationRunService,
    Depends(get_orchestration_run_service),
]
DashboardServiceDependency = Annotated[DashboardService, Depends(get_dashboard_service)]


def build_learning_goal(payload: LearningGoalCreate) -> LearningGoalDTO:
    now = datetime.now(tz=UTC)
    goal_token = uuid4().hex
    run_token = uuid4().hex
    learner_profile = payload.learner_profile or _default_learner_profile()
    normalized_goal_text = " ".join(payload.goal_text.split())

    return LearningGoalDTO(
        goal_id=f"goal_{goal_token}",
        run_id=f"run_{run_token}",
        goal_text=payload.goal_text,
        normalized_goal_text=normalized_goal_text,
        status=GoalStatus.CREATED,
        learner_profile=learner_profile,
        target_duration_weeks=None,
        hours_per_week=learner_profile.time_availability_hours_per_week,
        demo_seed_id="manual_demo_goal" if payload.demo_mode else None,
        created_at=now,
        updated_at=now,
    )


def reset_api_container_for_tests() -> None:
    _api_container.clear()


def _canonical_orchestration_run() -> OrchestrationRunDTO:
    return OrchestrationRunDTO(
        run_id=demo.RUN_ID,
        goal_id=demo.GOAL_ID,
        workflow_version="demo-v1",
        status=OrchestrationRunStatus.COMPLETED,
        current_node="prepare_dashboard_payload",
        completed_nodes=[
            "goal_loaded",
            "assessment_loaded",
            "knowledge_map_loaded",
            "curriculum_loaded",
            "dashboard_loaded",
        ],
        failed_nodes=[],
        node_events=[],
        artifact_ids={
            "goal_id": demo.GOAL_ID,
            "assessment_id": demo.ASSESSMENT_ID,
            "knowledge_map_id": demo.KNOWLEDGE_MAP_ID,
            "curriculum_id": demo.CURRICULUM_ID,
            "progress_id": demo.PROGRESS_ID,
            "quiz_id": demo.QUIZ_ID,
            "quiz_attempt_id": demo.QUIZ_ATTEMPT_ID,
            "adaptation_id": demo.ADAPTATION_ID,
            "critic_id": demo.CRITIC_REVIEW_ID,
            "evaluation_id": demo.EVALUATION_REPORT_ID,
        },
        started_at=demo.NOW,
        completed_at=demo.NOW,
        created_at=demo.NOW,
        updated_at=demo.NOW,
    )


def _default_learner_profile() -> LearnerProfile:
    return LearnerProfile(
        learner_type="local demo learner",
        strengths=[],
        weak_areas=[],
        time_availability_hours_per_week=6,
        desired_outcome="Explore the requested learning goal in local demo mode.",
        preferred_resource_types=[],
        difficulty_target=DifficultyLevel.INTERMEDIATE,
    )
