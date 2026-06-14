import os
from dataclasses import dataclass
from typing import Literal

from app.repositories.fakes import (
    FakeAdapterRepository,
    FakeAssessmentRepository,
    FakeCriticRepository,
    FakeCurriculumRepository,
    FakeEvaluationRepository,
    FakeProgressRepository,
    FakeQuizRepository,
    FakeResourceRepository,
)
from app.repositories.mongo import (
    MongoAdapterRepository,
    MongoAssessmentRepository,
    MongoCriticRepository,
    MongoCurriculumRepository,
    MongoEvaluationRepository,
    MongoProgressRepository,
    MongoQuizRepository,
    MongoResourceRepository,
)
from app.repositories.protocols import (
    AdapterRepository,
    AssessmentRepository,
    CriticRepository,
    CurriculumRepository,
    EvaluationRepository,
    ProgressRepository,
    QuizRepository,
    ResourceRepository,
)

RepositoryBackend = Literal["fake", "mongo"]
REPOSITORY_BACKEND_ENV = "PATHAI_REPOSITORY_BACKEND"


@dataclass(frozen=True)
class RepositoryBundle:
    assessment: AssessmentRepository
    curriculum: CurriculumRepository
    progress: ProgressRepository
    quiz: QuizRepository
    adapter: AdapterRepository
    critic: CriticRepository
    resource: ResourceRepository
    evaluation: EvaluationRepository


def configured_repository_backend() -> RepositoryBackend:
    raw_backend = os.getenv(REPOSITORY_BACKEND_ENV, "fake").strip().lower()
    return "mongo" if raw_backend == "mongo" else "fake"


def build_repository_bundle(
    backend: RepositoryBackend | None = None,
) -> RepositoryBundle:
    selected = backend or configured_repository_backend()
    if selected == "mongo":
        return RepositoryBundle(
            assessment=MongoAssessmentRepository(),
            curriculum=MongoCurriculumRepository(),
            progress=MongoProgressRepository(),
            quiz=MongoQuizRepository(),
            adapter=MongoAdapterRepository(),
            critic=MongoCriticRepository(),
            resource=MongoResourceRepository(),
            evaluation=MongoEvaluationRepository(),
        )
    return RepositoryBundle(
        assessment=FakeAssessmentRepository(),
        curriculum=FakeCurriculumRepository(),
        progress=FakeProgressRepository(),
        quiz=FakeQuizRepository(),
        adapter=FakeAdapterRepository(),
        critic=FakeCriticRepository(),
        resource=FakeResourceRepository(),
        evaluation=FakeEvaluationRepository(),
    )
