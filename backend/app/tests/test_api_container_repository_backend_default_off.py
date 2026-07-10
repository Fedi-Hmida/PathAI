from __future__ import annotations

from collections.abc import Iterator

import pytest

from app.api.v1.dependencies import ApiServiceContainer
from app.core.settings import get_settings
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


@pytest.fixture(autouse=True)
def _fresh_settings_cache(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("REPOSITORY_BACKEND", raising=False)
    monkeypatch.delenv("MONGODB_URI", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_api_container_defaults_to_fake_repositories_with_no_env_vars_set() -> None:
    container = ApiServiceContainer()

    assert isinstance(container.goal_repository, FakeGoalRepository)
    assert isinstance(container.assessment_repository, FakeAssessmentRepository)
    assert isinstance(container.knowledge_map_repository, FakeKnowledgeMapRepository)
    assert isinstance(container.curriculum_repository, FakeCurriculumRepository)
    assert isinstance(container.resource_repository, FakeResourceRepository)
    assert isinstance(container.progress_repository, FakeProgressRepository)
    assert isinstance(container.quiz_repository, FakeQuizRepository)
    assert isinstance(container.adaptation_repository, FakeAdaptationRepository)
    assert isinstance(container.critic_repository, FakeCriticReviewRepository)
    assert isinstance(container.evaluation_repository, FakeEvaluationRepository)
    assert isinstance(container.orchestration_run_repository, FakeOrchestrationRunRepository)


def test_api_container_load_canonical_demo_still_works_with_default_backend() -> None:
    container = ApiServiceContainer()

    response = container.load_canonical_demo()

    assert response.deterministic is True
