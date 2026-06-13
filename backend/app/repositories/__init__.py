"""Repository contracts and deterministic fake repositories."""

from app.repositories.fakes import (
    FakeAdapterRepository,
    FakeAssessmentRepository,
    FakeCriticRepository,
    FakeCurriculumRepository,
    FakeEvaluationRepository,
    FakeOrchestrationRepository,
    FakeProgressRepository,
    FakeQuizRepository,
    FakeResourceRepository,
)
from app.repositories.protocols import (
    AdapterRepository,
    AssessmentRepository,
    CriticRepository,
    CurriculumRepository,
    EvaluationRepository,
    OrchestrationRepository,
    ProgressRepository,
    QuizRepository,
    RepositoryPayload,
    ResourceRepository,
)

__all__ = [
    "AdapterRepository",
    "AssessmentRepository",
    "CriticRepository",
    "CurriculumRepository",
    "EvaluationRepository",
    "FakeAdapterRepository",
    "FakeAssessmentRepository",
    "FakeCriticRepository",
    "FakeCurriculumRepository",
    "FakeEvaluationRepository",
    "FakeOrchestrationRepository",
    "FakeProgressRepository",
    "FakeQuizRepository",
    "FakeResourceRepository",
    "OrchestrationRepository",
    "ProgressRepository",
    "QuizRepository",
    "RepositoryPayload",
    "ResourceRepository",
]
