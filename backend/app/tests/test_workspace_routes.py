from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import reset_api_container_for_tests
from app.core.settings import get_settings
from app.main import create_app


@pytest.fixture
def auth_enabled_app(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "workspace-test-secret-value-0123456789")
    monkeypatch.setenv("REFRESH_COOKIE_SECURE", "false")
    get_settings.cache_clear()
    reset_api_container_for_tests()
    yield
    get_settings.cache_clear()


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correcthorsebattery"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]  # type: ignore[no-any-return]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_workspace(
    client: TestClient,
    token: str,
    goal_text: str = "Learn watercolor painting for a small gallery show",
):
    return client.post(
        "/api/v1/me/workspace",
        headers=_auth_header(token),
        json={"goal_text": goal_text},
    )


def _reset_workspace(
    client: TestClient,
    token: str,
    goal_text: str = "Learn watercolor painting for a small gallery show",
):
    return client.post(
        "/api/v1/me/workspace/reset",
        headers=_auth_header(token),
        json={"goal_text": goal_text},
    )


def test_new_user_has_no_workspace_until_created(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")

    response = client.get("/api/v1/me/workspace", headers=_auth_header(token))

    assert response.status_code == 404


def test_create_workspace_then_dashboard_is_populated(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")

    create_response = _create_workspace(client, token)
    assert create_response.status_code == 201
    run_id = create_response.json()["run_id"]

    get_response = client.get("/api/v1/me/workspace", headers=_auth_header(token))
    assert get_response.status_code == 200
    assert get_response.json()["run_id"] == run_id

    dashboard_response = client.get(
        f"/api/v1/dashboard/{run_id}",
        headers=_auth_header(token),
    )
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["run_summary"]["run_id"] == run_id


def test_creating_a_second_workspace_for_the_same_user_is_rejected(
    auth_enabled_app: None,
) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    _create_workspace(client, token)

    second = _create_workspace(client, token)

    assert second.status_code == 409


def test_two_users_get_isolated_workspaces_and_cannot_read_each_others(
    auth_enabled_app: None,
) -> None:
    client = TestClient(create_app())
    token_a = _register(client, "alice@example.com")
    token_b = _register(client, "bob@example.com")

    run_a = _create_workspace(client, token_a).json()["run_id"]
    run_b = _create_workspace(client, token_b).json()["run_id"]

    assert run_a != run_b

    # Alice can read her own dashboard.
    own_response = client.get(f"/api/v1/dashboard/{run_a}", headers=_auth_header(token_a))
    assert own_response.status_code == 200

    # Bob cannot read Alice's dashboard/run/goal - scoped 404, not 403.
    cross_dashboard = client.get(f"/api/v1/dashboard/{run_a}", headers=_auth_header(token_b))
    assert cross_dashboard.status_code == 404

    alice_goal_id = own_response.json()["goal_summary"]["goal_id"]
    cross_goal = client.get(f"/api/v1/goals/{alice_goal_id}", headers=_auth_header(token_b))
    assert cross_goal.status_code == 404

    cross_run = client.get(
        f"/api/v1/orchestration/runs/{run_a}",
        headers=_auth_header(token_b),
    )
    assert cross_run.status_code == 404


def test_reset_replaces_workspace_with_a_fresh_one(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    original_run_id = _create_workspace(client, token).json()["run_id"]

    reset_response = _reset_workspace(client, token, goal_text="Learn oil painting instead")

    assert reset_response.status_code == 200
    new_run_id = reset_response.json()["run_id"]
    assert new_run_id != original_run_id
    # The old run is gone.
    stale = client.get(f"/api/v1/orchestration/runs/{original_run_id}", headers=_auth_header(token))
    assert stale.status_code == 404
    # The new one is reachable.
    fresh = client.get(f"/api/v1/orchestration/runs/{new_run_id}", headers=_auth_header(token))
    assert fresh.status_code == 200


def test_demo_load_fixtures_is_disabled_while_auth_enabled(auth_enabled_app: None) -> None:
    client = TestClient(create_app())

    response = client.post("/api/v1/demo/load-fixtures")

    assert response.status_code == 404


def test_orchestration_run_trigger_is_disabled_while_auth_enabled(auth_enabled_app: None) -> None:
    client = TestClient(create_app())

    response = client.post("/api/v1/orchestration/runs")

    assert response.status_code == 404


def test_workspace_routes_are_hidden_when_auth_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "false")
    get_settings.cache_clear()
    reset_api_container_for_tests()
    client = TestClient(create_app())

    response = client.get("/api/v1/me/workspace")

    assert response.status_code == 404
    get_settings.cache_clear()


def test_demo_load_fixtures_still_works_when_auth_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "false")
    get_settings.cache_clear()
    reset_api_container_for_tests()
    client = TestClient(create_app())

    response = client.post("/api/v1/demo/load-fixtures")

    assert response.status_code == 200
    get_settings.cache_clear()
