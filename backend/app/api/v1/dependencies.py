from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, HTTPException, Request

from app.api.v1.responses import DemoLoadFixturesResponse
from app.core.settings import Settings, get_settings
from app.fixtures import canonical_demo as demo
from app.orchestration.runner import run_straight_line_demo_from_container
from app.repositories.factory import build_repository_set
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
    RefreshTokenRepository,
    ResourceRepository,
    UserRepository,
)
from app.schemas.auth import UserDTO
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
    AuthorizationService,
    AuthService,
    AuthTokenConfig,
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
    WorkspaceService,
)
from app.services.auth import TokenRejectedError


@dataclass(slots=True)
class ApiServiceContainer:
    goal_repository: GoalRepository = field(init=False)
    assessment_repository: AssessmentRepository = field(init=False)
    knowledge_map_repository: KnowledgeMapRepository = field(init=False)
    curriculum_repository: CurriculumRepository = field(init=False)
    resource_repository: ResourceRepository = field(init=False)
    progress_repository: ProgressRepository = field(init=False)
    quiz_repository: QuizRepository = field(init=False)
    adaptation_repository: AdaptationRepository = field(init=False)
    critic_repository: CriticReviewRepository = field(init=False)
    evaluation_repository: EvaluationRepository = field(init=False)
    orchestration_run_repository: OrchestrationRunRepository = field(init=False)
    user_repository: UserRepository = field(init=False)
    refresh_token_repository: RefreshTokenRepository = field(init=False)
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
    workspace_service: WorkspaceService = field(init=False)

    def __post_init__(self) -> None:
        repositories = build_repository_set(get_settings())
        self.goal_repository = repositories.goal
        self.assessment_repository = repositories.assessment
        self.knowledge_map_repository = repositories.knowledge_map
        self.curriculum_repository = repositories.curriculum
        self.resource_repository = repositories.resource
        self.progress_repository = repositories.progress
        self.quiz_repository = repositories.quiz
        self.adaptation_repository = repositories.adaptation
        self.critic_repository = repositories.critic
        self.evaluation_repository = repositories.evaluation
        self.orchestration_run_repository = repositories.orchestration_run
        self.user_repository = repositories.user
        self.refresh_token_repository = repositories.refresh_token
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
        self.workspace_service = WorkspaceService(
            goals=self.goal_repository,
            orchestration_runs=self.orchestration_run_repository,
            assessments=self.assessment_repository,
            knowledge_maps=self.knowledge_map_repository,
            curricula=self.curriculum_repository,
            resources=self.resource_repository,
            progress_states=self.progress_repository,
            quizzes=self.quiz_repository,
            adaptations=self.adaptation_repository,
            critics=self.critic_repository,
            evaluations=self.evaluation_repository,
        )

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
        self.user_repository.clear()
        self.refresh_token_repository.clear()

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

    def run_demo_pipeline(self) -> OrchestrationRunDTO:
        return run_straight_line_demo_from_container(self).run


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


SettingsDependency = Annotated[Settings, Depends(get_settings)]


class AuthConfigError(RuntimeError):
    """Raised when auth is enabled but no signing secret is configured."""


def _build_auth_token_config(settings: Settings) -> AuthTokenConfig:
    secret = settings.jwt_secret_key
    if secret is None:
        raise AuthConfigError(
            "JWT_SECRET_KEY is required when PATHAI_ENABLE_AUTH is true",
        )
    return AuthTokenConfig(
        secret=secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
        access_ttl_seconds=settings.access_token_ttl_seconds,
        refresh_ttl_seconds=settings.refresh_token_ttl_seconds,
    )


def _auth_service(container: ApiServiceContainer, settings: Settings) -> AuthService:
    return AuthService(
        users=container.user_repository,
        refresh_tokens=container.refresh_token_repository,
        config=_build_auth_token_config(settings),
    )


def get_auth_service(
    container: ApiContainerDependency,
    settings: SettingsDependency,
) -> AuthService:
    return _auth_service(container, settings)


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]


def require_auth_enabled(settings: SettingsDependency) -> None:
    """Make auth routes invisible (404) unless PATHAI_ENABLE_AUTH is on."""
    if not settings.enable_auth:
        raise HTTPException(status_code=404, detail="resource not found")


def require_auth_disabled(settings: SettingsDependency) -> None:
    """Guard shared-state routes that must not run while auth is enabled.

    The demo fixture loader clears ALL data; with per-user workspaces active it
    would wipe every user's data, so it is hidden (404) when auth is on.
    """
    if settings.enable_auth:
        raise HTTPException(status_code=404, detail="resource not found")


def get_workspace_service(container: ApiContainerDependency) -> WorkspaceService:
    return container.workspace_service


WorkspaceServiceDependency = Annotated[WorkspaceService, Depends(get_workspace_service)]


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("Authorization")
    if not header or not header.lower().startswith("bearer "):
        return None
    return header[len("bearer ") :].strip() or None


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_user(
    request: Request,
    settings: SettingsDependency,
    container: ApiContainerDependency,
) -> UserDTO | None:
    """Router-level guard.

    When auth is disabled this is a no-op (returns None) so the local demo and
    existing routes behave exactly as before. When enabled, a valid bearer
    access token is required or the request is rejected with 401.
    """
    if not settings.enable_auth:
        return None
    token = _bearer_token(request)
    if token is None:
        raise _unauthorized()
    try:
        return _auth_service(container, settings).resolve_access(token)
    except TokenRejectedError:
        raise _unauthorized() from None


CurrentUserOrNoneDependency = Annotated[UserDTO | None, Depends(require_user)]


def get_current_user(user: CurrentUserOrNoneDependency) -> UserDTO:
    """Strict variant for endpoints that always need an authenticated user."""
    if user is None:
        raise _unauthorized()
    return user


CurrentUserDependency = Annotated[UserDTO, Depends(get_current_user)]


def get_authorization_service(container: ApiContainerDependency) -> AuthorizationService:
    return AuthorizationService(container.goal_repository)


AuthorizationDependency = Annotated[AuthorizationService, Depends(get_authorization_service)]


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
