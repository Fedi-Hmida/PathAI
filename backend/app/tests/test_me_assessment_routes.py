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
    monkeypatch.setenv("JWT_SECRET_KEY", "me-assessment-test-secret-value-0123456789")
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


def test_fresh_workspace_has_no_assessment_session(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    client.post("/api/v1/me/workspace", headers=_auth_header(token))

    response = client.get("/api/v1/me/assessment", headers=_auth_header(token))

    assert response.status_code == 404


def test_dashboard_for_a_fresh_workspace_has_no_assessment_summary(
    auth_enabled_app: None,
) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    run_id = client.post(
        "/api/v1/me/workspace",
        headers=_auth_header(token),
    ).json()["run_id"]

    dashboard = client.get(f"/api/v1/dashboard/{run_id}", headers=_auth_header(token))

    assert dashboard.status_code == 200
    assert dashboard.json()["assessment_summary"] is None


def test_start_then_full_turn_by_turn_sequence_reaches_completed(
    auth_enabled_app: None,
) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    client.post("/api/v1/me/workspace", headers=_auth_header(token))

    start_response = client.post("/api/v1/me/assessment/start", headers=_auth_header(token))
    assert start_response.status_code == 201
    session = start_response.json()
    assert session["status"] == "in_progress"
    assessment_id = session["assessment_session_id"]
    seen_question_ids = [session["current_question"]["question_id"]]

    current_status = "in_progress"
    for _ in range(5):
        current_question_id = seen_question_ids[-1]
        answer_response = client.post(
            f"/api/v1/me/assessment/{assessment_id}/answer",
            headers=_auth_header(token),
            json={"question_id": current_question_id, "selected_options": [], "self_rating": 3},
        )
        assert answer_response.status_code == 200
        body = answer_response.json()
        assert body["answer"]["question"]["question_id"] == current_question_id
        current_status = body["session"]["status"]
        next_question = body["session"]["current_question"]
        if next_question is not None:
            seen_question_ids.append(next_question["question_id"])

    assert current_status == "completed"
    assert len(seen_question_ids) == len(set(seen_question_ids))

    get_response = client.get("/api/v1/me/assessment", headers=_auth_header(token))
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "completed"


def test_start_is_idempotent_over_http(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    client.post("/api/v1/me/workspace", headers=_auth_header(token))

    first = client.post("/api/v1/me/assessment/start", headers=_auth_header(token))
    second = client.post("/api/v1/me/assessment/start", headers=_auth_header(token))

    assert first.json()["assessment_session_id"] == second.json()["assessment_session_id"]


def test_start_without_a_workspace_is_not_found(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")

    response = client.post("/api/v1/me/assessment/start", headers=_auth_header(token))

    assert response.status_code == 404


def test_non_owner_cannot_answer_someone_elses_assessment(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token_a = _register(client, "alice@example.com")
    token_b = _register(client, "bob@example.com")
    client.post("/api/v1/me/workspace", headers=_auth_header(token_a))
    client.post("/api/v1/me/workspace", headers=_auth_header(token_b))

    session_a = client.post(
        "/api/v1/me/assessment/start",
        headers=_auth_header(token_a),
    ).json()
    assessment_id = session_a["assessment_session_id"]
    question_id = session_a["current_question"]["question_id"]

    cross_answer = client.post(
        f"/api/v1/me/assessment/{assessment_id}/answer",
        headers=_auth_header(token_b),
        json={"question_id": question_id},
    )

    assert cross_answer.status_code == 404


def test_me_assessment_routes_are_hidden_when_auth_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "false")
    get_settings.cache_clear()
    reset_api_container_for_tests()
    client = TestClient(create_app())

    response = client.get("/api/v1/me/assessment")

    assert response.status_code == 404
    get_settings.cache_clear()


def test_no_auth_demo_assessment_read_routes_are_unaffected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "false")
    get_settings.cache_clear()
    reset_api_container_for_tests()
    client = TestClient(create_app())
    client.post("/api/v1/demo/load-fixtures")

    response = client.get("/api/v1/assessments/assessment_demo_rag")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    get_settings.cache_clear()
