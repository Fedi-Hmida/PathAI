from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from app.api.v1.dependencies import ApiServiceContainer
from app.core.settings import Settings, get_settings
from app.fixtures import canonical_demo as demo

ENABLE_LIVE_MONGO_TESTS = "ENABLE_LIVE_MONGO_TESTS"

pytestmark = pytest.mark.skipif(
    os.getenv(ENABLE_LIVE_MONGO_TESTS, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live MongoDB checks are optional and require "
        f"{ENABLE_LIVE_MONGO_TESTS}=1."
    ),
)


@pytest.fixture
def _mongo_backend_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    if not Settings().mongodb_uri:
        pytest.skip("MONGODB_URI is not configured.")
    monkeypatch.setenv("REPOSITORY_BACKEND", "mongo")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.live_mongo
def test_api_container_persists_canonical_demo_to_real_mongo_and_a_fresh_container_reads_it_back(
    _mongo_backend_env: None,
) -> None:
    writer_container = ApiServiceContainer()
    try:
        # load_canonical_demo() calls clear() first, which wipes the configured
        # database's production-shaped collections (not test-prefixed) before
        # reloading — this test is meant to exercise the real wiring path end
        # to end, so it deliberately does not use scratch collection names.
        response = writer_container.load_canonical_demo()
        assert response.deterministic is True
        assert response.dashboard_payload is not None

        reader_container = ApiServiceContainer()
        goal = reader_container.goal_service.get_by_id(demo.GOAL_ID)
        assert goal.goal_id == demo.GOAL_ID

        curriculum = reader_container.curriculum_service.get_by_id(demo.CURRICULUM_ID)
        assert curriculum.curriculum_id == demo.CURRICULUM_ID
        assert len(curriculum.weeks) > 0
    finally:
        writer_container.clear()
