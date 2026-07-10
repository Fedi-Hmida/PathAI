from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import ApiServiceContainer, get_api_container
from app.core.settings import Settings, get_settings
from app.fixtures import canonical_demo as demo
from app.main import create_app
from app.schemas.enums import OrchestrationRunStatus

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
def test_route_triggered_run_persists_to_real_mongo_and_an_independent_container_reads_it_back(
    _mongo_backend_env: None,
) -> None:
    # The module-level ApiServiceContainer singleton (app.api.v1.dependencies.
    # _api_container) is constructed once, at import time, under whatever
    # backend was configured then -- long before this test's monkeypatched env
    # exists. A FastAPI dependency override swaps in a container genuinely
    # built under REPOSITORY_BACKEND=mongo for the request, without touching
    # that singleton or any application code -- the route handler itself is
    # unmodified.
    writer_container = ApiServiceContainer()
    app = create_app()
    app.dependency_overrides[get_api_container] = lambda: writer_container
    client = TestClient(app)

    try:
        response = client.post("/api/v1/orchestration/runs")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["run_id"] == demo.RUN_ID

        # A second, independently constructed container -- the one property a
        # fake/in-memory repository can never demonstrate.
        reader_container = ApiServiceContainer()
        run = reader_container.orchestration_run_service.get_by_id(demo.RUN_ID)
        assert run.run_id == demo.RUN_ID
        assert run.status == OrchestrationRunStatus.COMPLETED

        goal = reader_container.goal_service.get_by_id(demo.GOAL_ID)
        assert goal.goal_id == demo.GOAL_ID
    finally:
        writer_container.clear()
