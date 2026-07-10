from __future__ import annotations

from dataclasses import dataclass

from app.core.settings import Settings
from app.db.mongo_client import build_mongo_client_from_settings
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
from app.repositories.mongo import (
    MongoAdaptationRepository,
    MongoAssessmentRepository,
    MongoCriticReviewRepository,
    MongoCurriculumRepository,
    MongoEvaluationRepository,
    MongoGoalRepository,
    MongoKnowledgeMapRepository,
    MongoOrchestrationRunRepository,
    MongoProgressRepository,
    MongoQuizRepository,
    MongoResourceRepository,
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

_FAKE_BACKEND = "fake"
_MONGO_BACKEND = "mongo"


class RepositoryBackendConfigError(RuntimeError):
    """Raised when Settings.repository_backend is not a recognized value."""


@dataclass(slots=True, frozen=True)
class RepositorySet:
    goal: GoalRepository
    assessment: AssessmentRepository
    knowledge_map: KnowledgeMapRepository
    curriculum: CurriculumRepository
    resource: ResourceRepository
    progress: ProgressRepository
    quiz: QuizRepository
    adaptation: AdaptationRepository
    critic: CriticReviewRepository
    evaluation: EvaluationRepository
    orchestration_run: OrchestrationRunRepository


def build_repository_set(settings: Settings) -> RepositorySet:
    backend = settings.repository_backend.strip().lower()
    if backend == _FAKE_BACKEND:
        return _build_fake_repository_set()
    if backend == _MONGO_BACKEND:
        return _build_mongo_repository_set(settings)
    msg = f"Unrecognized repository_backend: {backend!r} (expected 'fake' or 'mongo')"
    raise RepositoryBackendConfigError(msg)


def _build_fake_repository_set() -> RepositorySet:
    return RepositorySet(
        goal=FakeGoalRepository(),
        assessment=FakeAssessmentRepository(),
        knowledge_map=FakeKnowledgeMapRepository(),
        curriculum=FakeCurriculumRepository(),
        resource=FakeResourceRepository(),
        progress=FakeProgressRepository(),
        quiz=FakeQuizRepository(),
        adaptation=FakeAdaptationRepository(),
        critic=FakeCriticReviewRepository(),
        evaluation=FakeEvaluationRepository(),
        orchestration_run=FakeOrchestrationRunRepository(),
    )


def _build_mongo_repository_set(settings: Settings) -> RepositorySet:
    client = build_mongo_client_from_settings(settings)
    database = client[settings.mongodb_database_name]
    return RepositorySet(
        goal=MongoGoalRepository(database["learning_goals"]),
        assessment=MongoAssessmentRepository(
            database["assessment_sessions"],
            database["assessment_answers"],
        ),
        knowledge_map=MongoKnowledgeMapRepository(database["knowledge_maps"]),
        curriculum=MongoCurriculumRepository(database["curricula"]),
        resource=MongoResourceRepository(
            database["resources"],
            database["resource_attachments"],
        ),
        progress=MongoProgressRepository(database["progress_states"]),
        quiz=MongoQuizRepository(database["quizzes"], database["quiz_attempts"]),
        adaptation=MongoAdaptationRepository(database["adaptation_events"]),
        critic=MongoCriticReviewRepository(database["critic_reviews"]),
        evaluation=MongoEvaluationRepository(database["evaluation_reports"]),
        orchestration_run=MongoOrchestrationRunRepository(database["orchestration_runs"]),
    )
