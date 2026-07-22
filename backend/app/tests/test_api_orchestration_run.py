from __future__ import annotations

from collections.abc import Iterator

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


@pytest.fixture
def auth_enabled_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "orchestration-test-secret-value-0123456789")
    monkeypatch.setenv("REFRESH_COOKIE_SECURE", "false")
    get_settings.cache_clear()
    reset_api_container_for_tests()
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


@pytest.mark.parametrize("route_flag", ["true", "false"])
def test_post_orchestration_runs_returns_404_when_auth_enabled(
    auth_enabled_app: None,
    monkeypatch: pytest.MonkeyPatch,
    route_flag: str,
) -> None:
    # The auth gate must 404 the demo trigger regardless of
    # enable_orchestration_run_route's value - it belongs to the retired
    # no-auth demo mode and must never be reachable once auth is on.
    monkeypatch.setenv("PATHAI_ENABLE_ORCHESTRATION_RUN_ROUTE", route_flag)
    client = TestClient(create_app())

    response = client.post("/api/v1/orchestration/runs")

    assert response.status_code == 404


def test_post_orchestration_runs_still_respects_route_flag_when_auth_disabled() -> None:
    # Pre-existing no-auth-demo behavior must be unchanged by the new gate.
    client = _client()

    enabled_response = client.post("/api/v1/orchestration/runs")
    assert enabled_response.status_code == 200


def test_get_orchestration_run_routes_unaffected_by_auth_enabled(
    auth_enabled_app: None,
) -> None:
    # The two GET routes must remain reachable (and, per
    # test_workspace_routes.py's cross-user coverage, still
    # ownership-scoped) - only the POST trigger is gated by this step.
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    create_response = client.post(
        "/api/v1/me/workspace",
        headers=headers,
        json={"goal_text": "Learn classical guitar for a recital"},
    )
    assert create_response.status_code == 201
    run_id = create_response.json()["run_id"]

    run_response = client.get(f"/api/v1/orchestration/runs/{run_id}", headers=headers)
    status_response = client.get(f"/api/v1/orchestration/runs/{run_id}/status", headers=headers)

    assert run_response.status_code == 200
    assert status_response.status_code == 200


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correcthorsebattery"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]  # type: ignore[no-any-return]


def _client() -> TestClient:
    reset_api_container_for_tests()
    return TestClient(create_app())
