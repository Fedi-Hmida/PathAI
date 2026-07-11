from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import reset_api_container_for_tests
from app.core.settings import get_settings
from app.main import create_app

REGISTER_PAYLOAD = {"email": "learner@example.com", "password": "correcthorsebattery"}


@pytest.fixture
def auth_enabled_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "route-test-secret-value-0123456789")
    # Cookie must be sendable over the TestClient's plain-http test server.
    monkeypatch.setenv("REFRESH_COOKIE_SECURE", "false")
    get_settings.cache_clear()
    reset_api_container_for_tests()
    yield TestClient(create_app())
    get_settings.cache_clear()


@pytest.fixture
def auth_disabled_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "false")
    get_settings.cache_clear()
    reset_api_container_for_tests()
    yield TestClient(create_app())
    get_settings.cache_clear()


def test_register_then_me_round_trip(auth_enabled_client: TestClient) -> None:
    client = auth_enabled_client

    register_response = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert register_response.status_code == 201
    body = register_response.json()
    assert body["user"]["email"] == "learner@example.com"
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]
    assert client.cookies.get("pathai_refresh")

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "learner@example.com"


def test_register_duplicate_email_returns_409(auth_enabled_client: TestClient) -> None:
    client = auth_enabled_client
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    response = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 409


def test_login_wrong_password_returns_401_generic_message(auth_enabled_client: TestClient) -> None:
    client = auth_enabled_client
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "learner@example.com", "password": "totally-wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid email or password"


def test_login_unknown_email_returns_same_generic_message(auth_enabled_client: TestClient) -> None:
    client = auth_enabled_client

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever12345"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "invalid email or password"


def test_me_without_token_returns_401(auth_enabled_client: TestClient) -> None:
    response = auth_enabled_client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_refresh_rotates_cookie_and_old_cookie_is_rejected(
    auth_enabled_client: TestClient,
) -> None:
    client = auth_enabled_client
    register_response = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    original_cookie = register_response.cookies.get("pathai_refresh")

    refresh_response = client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == 200

    client.cookies.set("pathai_refresh", original_cookie)
    replay_response = client.post("/api/v1/auth/refresh")
    assert replay_response.status_code == 401


def test_logout_revokes_session(auth_enabled_client: TestClient) -> None:
    client = auth_enabled_client
    client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 204

    refresh_after_logout = client.post("/api/v1/auth/refresh")
    assert refresh_after_logout.status_code == 401


def test_auth_routes_are_hidden_when_flag_disabled(auth_disabled_client: TestClient) -> None:
    response = auth_disabled_client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 404


def test_existing_goal_route_is_unaffected_when_auth_flag_disabled(
    auth_disabled_client: TestClient,
) -> None:
    response = auth_disabled_client.post(
        "/api/v1/goals",
        json={"goal_text": "Learn reliable prompt evaluation for a class project"},
    )

    assert response.status_code == 201
