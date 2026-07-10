from __future__ import annotations

import pytest

from app.core.settings import Settings
from app.db.mongo_client import MongoNotConfiguredError
from app.repositories.factory import RepositoryBackendConfigError, build_repository_set
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


def test_repository_backend_defaults_to_fake() -> None:
    assert Settings().repository_backend == "fake"


def test_build_repository_set_fake_backend_returns_fake_repositories() -> None:
    repositories = build_repository_set(Settings(repository_backend="fake"))

    assert isinstance(repositories.goal, FakeGoalRepository)
    assert isinstance(repositories.assessment, FakeAssessmentRepository)
    assert isinstance(repositories.knowledge_map, FakeKnowledgeMapRepository)
    assert isinstance(repositories.curriculum, FakeCurriculumRepository)
    assert isinstance(repositories.resource, FakeResourceRepository)
    assert isinstance(repositories.progress, FakeProgressRepository)
    assert isinstance(repositories.quiz, FakeQuizRepository)
    assert isinstance(repositories.adaptation, FakeAdaptationRepository)
    assert isinstance(repositories.critic, FakeCriticReviewRepository)
    assert isinstance(repositories.evaluation, FakeEvaluationRepository)
    assert isinstance(repositories.orchestration_run, FakeOrchestrationRunRepository)


def test_build_repository_set_mongo_backend_without_uri_fails_closed() -> None:
    settings = Settings(repository_backend="mongo", mongodb_uri="")

    with pytest.raises(MongoNotConfiguredError):
        build_repository_set(settings)


def test_build_repository_set_unrecognized_backend_raises_config_error() -> None:
    settings = Settings(repository_backend="postgres")

    with pytest.raises(RepositoryBackendConfigError):
        build_repository_set(settings)


def test_build_repository_set_backend_selection_is_case_insensitive() -> None:
    settings = Settings(repository_backend="FAKE")

    repositories = build_repository_set(settings)

    assert isinstance(repositories.goal, FakeGoalRepository)
