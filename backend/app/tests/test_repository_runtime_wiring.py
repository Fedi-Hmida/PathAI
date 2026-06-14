from __future__ import annotations

from collections.abc import Iterator
from importlib import import_module, reload
from typing import Any, cast

import pytest

from app.api.v1.runtime_services import build_runtime_services
from app.repositories import (
    REPOSITORY_BACKEND_ENV,
    FakeAssessmentRepository,
    MongoAssessmentRepository,
    build_repository_bundle,
    configured_repository_backend,
)
from app.repositories.runtime import get_repository_bundle, reset_repository_bundle_for_tests


@pytest.fixture(autouse=True)
def reset_runtime_bundle() -> Iterator[None]:
    reset_repository_bundle_for_tests()
    yield
    reset_repository_bundle_for_tests()


def _repository_from_store(service: object) -> object:
    service_with_store = cast(Any, service)
    return service_with_store.store.repository


def test_runtime_bundle_defaults_to_fake_repositories(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(REPOSITORY_BACKEND_ENV, raising=False)

    bundle = get_repository_bundle()

    assert configured_repository_backend() == "fake"
    assert isinstance(bundle.assessment, FakeAssessmentRepository)
    assert get_repository_bundle() is bundle


def test_runtime_bundle_can_select_mongo_without_live_atlas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(REPOSITORY_BACKEND_ENV, "mongo")

    bundle = get_repository_bundle()

    assert configured_repository_backend() == "mongo"
    assert isinstance(bundle.assessment, MongoAssessmentRepository)
    assert get_repository_bundle() is bundle


def test_unknown_runtime_backend_falls_back_to_fake(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(REPOSITORY_BACKEND_ENV, "unknown")

    bundle = get_repository_bundle()

    assert configured_repository_backend() == "fake"
    assert isinstance(bundle.assessment, FakeAssessmentRepository)


def test_build_runtime_services_uses_one_repository_bundle() -> None:
    bundle = build_repository_bundle("fake")

    services = build_runtime_services(bundle)

    assert _repository_from_store(services.assessment) is bundle.assessment
    assert _repository_from_store(services.curriculum) is bundle.curriculum
    assert _repository_from_store(services.progress) is bundle.progress
    assert _repository_from_store(services.quiz) is bundle.quiz
    assert _repository_from_store(services.adapter) is bundle.adapter
    assert _repository_from_store(services.critic) is bundle.critic
    assert _repository_from_store(services.resources) is bundle.resource
    assert _repository_from_store(services.evaluation) is bundle.evaluation
    assert _repository_from_store(services.adapter.resource_service) is bundle.resource
    assert _repository_from_store(services.adapter.critic_service) is bundle.critic


def test_route_level_services_are_repository_backed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(REPOSITORY_BACKEND_ENV, raising=False)
    reset_repository_bundle_for_tests()

    assessment_route = reload(import_module("app.api.v1.assessment"))
    curriculum_route = reload(import_module("app.api.v1.curriculum"))
    progress_route = reload(import_module("app.api.v1.progress"))
    quiz_route = reload(import_module("app.api.v1.quiz"))
    resources_route = reload(import_module("app.api.v1.resources"))
    critic_route = reload(import_module("app.api.v1.critic"))
    adapt_route = reload(import_module("app.api.v1.adapt"))
    evaluation_route = reload(import_module("app.api.v1.evaluation"))
    dev_route = reload(import_module("app.api.v1.dev"))
    bundle = get_repository_bundle()

    route_expectations: list[tuple[Any, object]] = [
        (assessment_route.assessment_service, bundle.assessment),
        (curriculum_route.curriculum_service, bundle.curriculum),
        (progress_route.progress_service, bundle.progress),
        (quiz_route.quiz_service, bundle.quiz),
        (resources_route.resource_service, bundle.resource),
        (critic_route.critic_service, bundle.critic),
        (adapt_route.adapter_service, bundle.adapter),
        (evaluation_route.evaluation_service, bundle.evaluation),
        (dev_route.curriculum_dev_service, bundle.curriculum),
        (dev_route.resource_dev_service, bundle.resource),
        (dev_route.critic_dev_service, bundle.critic),
        (dev_route.progress_dev_service, bundle.progress),
        (dev_route.quiz_dev_service, bundle.quiz),
        (dev_route.adapter_dev_service, bundle.adapter),
        (dev_route.evaluation_dev_service, bundle.evaluation),
    ]
    for service, repository in route_expectations:
        assert _repository_from_store(service) is repository
    assert _repository_from_store(adapt_route.adapter_service.resource_service) is (
        bundle.resource
    )
    assert _repository_from_store(adapt_route.adapter_service.critic_service) is bundle.critic


def test_runtime_bundle_can_be_reset_for_tests() -> None:
    first = get_repository_bundle()
    replacement = build_repository_bundle("fake")

    reset_repository_bundle_for_tests(replacement)

    assert get_repository_bundle() is replacement
    assert get_repository_bundle() is not first
