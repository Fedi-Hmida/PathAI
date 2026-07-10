from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import reset_api_container_for_tests
from app.core.settings import get_settings
from app.fixtures import canonical_demo as demo
from app.main import create_app


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_post_orchestration_runs_returns_completed_run_and_is_readable_via_get() -> None:
    client = _client()

    post_response = client.post("/api/v1/orchestration/runs")
    assert post_response.status_code == 200
    body = post_response.json()
    assert body["status"] == "completed"
    assert body["run_id"] == demo.RUN_ID
    assert body["goal_id"] == demo.GOAL_ID
    assert body["failed_nodes"] == []

    get_response = client.get(f"/api/v1/orchestration/runs/{demo.RUN_ID}")
    assert get_response.status_code == 200
    assert get_response.json() == body


def test_post_orchestration_runs_returns_404_when_route_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_ORCHESTRATION_RUN_ROUTE", "false")
    client = _client()

    response = client.post("/api/v1/orchestration/runs")

    assert response.status_code == 404


def test_other_routes_unaffected_by_orchestration_run_route() -> None:
    client = _client()

    demo_response = client.post("/api/v1/demo/load-fixtures")
    assert demo_response.status_code == 200

    health_response = client.get("/api/v1/health")
    assert health_response.status_code == 200


def _client() -> TestClient:
    reset_api_container_for_tests()
    return TestClient(create_app())
