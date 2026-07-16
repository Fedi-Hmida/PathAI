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
    monkeypatch.setenv("JWT_SECRET_KEY", "workspace-generation-test-secret-0123456789")
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
    goal_text: str = "Learn classical guitar for a wedding performance",
):
    return client.post(
        "/api/v1/me/workspace",
        headers=_auth_header(token),
        json={"goal_text": goal_text},
    )


def _complete_assessment(client: TestClient, token: str) -> None:
    start = client.post("/api/v1/me/assessment/start", headers=_auth_header(token))
    assessment_id = start.json()["assessment_session_id"]
    question_id = start.json()["current_question"]["question_id"]
    for _ in range(5):
        response = client.post(
            f"/api/v1/me/assessment/{assessment_id}/answer",
            headers=_auth_header(token),
            json={"question_id": question_id, "selected_options": [], "self_rating": 3},
        )
        next_question = response.json()["session"]["current_question"]
        if next_question is not None:
            question_id = next_question["question_id"]


def test_generate_without_a_workspace_is_not_found(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")

    response = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))

    assert response.status_code == 404


def test_generate_before_assessment_completes_is_a_conflict(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    _create_workspace(client, token)

    response = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))

    assert response.status_code == 409


def test_generate_before_assessment_seeds_no_demo_clone_content(
    auth_enabled_app: None,
) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    goal_text = "Learn classical guitar for a wedding performance"
    run_id = _create_workspace(client, token, goal_text=goal_text).json()["run_id"]

    dashboard_before = client.get(
        f"/api/v1/dashboard/{run_id}",
        headers=_auth_header(token),
    ).json()

    assert dashboard_before["goal_summary"]["text"] == goal_text
    assert dashboard_before["run_summary"]["status"] == "queued"
    artifact_ids = dashboard_before["navigation_summary"]["artifact_ids"]
    assert "knowledge_map_id" not in artifact_ids
    assert "curriculum_id" not in artifact_ids
    assert dashboard_before["knowledge_map_summary"] is None
    assert dashboard_before["curriculum_summary"] is None
    assert dashboard_before["quiz_summary"] is None
    assert dashboard_before["critic_summary"] is None
    assert dashboard_before["evaluation_summary"] is None
    assert dashboard_before["progress_summary"] is None
    assert dashboard_before["resources_summary"]["total_attached"] == 0


def test_generate_after_completed_assessment_creates_fresh_real_content(
    auth_enabled_app: None,
) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    goal_text = "Learn classical guitar for a wedding performance"
    run_id = _create_workspace(client, token, goal_text=goal_text).json()["run_id"]

    _complete_assessment(client, token)

    response = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))

    assert response.status_code == 200
    body = response.json()
    # Fresh IDs, never the canonical demo's.
    assert body["knowledge_map_id"] != "kmap_demo_rag"
    assert body["curriculum_id"] != "curriculum_demo_rag_v1"

    dashboard_after = client.get(
        f"/api/v1/dashboard/{run_id}",
        headers=_auth_header(token),
    ).json()
    assert dashboard_after["assessment_summary"] is not None
    assert dashboard_after["goal_summary"]["text"] == goal_text
    assert dashboard_after["knowledge_map_summary"] is not None
    assert dashboard_after["curriculum_summary"] is not None
    artifact_ids = dashboard_after["navigation_summary"]["artifact_ids"]
    assert artifact_ids["knowledge_map_id"] == body["knowledge_map_id"]
    assert artifact_ids["curriculum_id"] == body["curriculum_id"]
    # The other six tiles stay honestly empty - Step 2 (out of scope here).
    assert dashboard_after["quiz_summary"] is None
    assert dashboard_after["critic_summary"] is None
    assert dashboard_after["evaluation_summary"] is None
    assert dashboard_after["progress_summary"] is None
    assert dashboard_after["resources_summary"]["total_attached"] == 0


def test_generate_is_callable_again_and_still_succeeds(auth_enabled_app: None) -> None:
    client = TestClient(create_app())
    token = _register(client, "learner@example.com")
    _create_workspace(client, token)
    _complete_assessment(client, token)

    first = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))
    second = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_workspace_generate_route_is_hidden_when_auth_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "false")
    get_settings.cache_clear()
    reset_api_container_for_tests()
    client = TestClient(create_app())

    response = client.post("/api/v1/me/workspace/generate")

    assert response.status_code == 404
    get_settings.cache_clear()
