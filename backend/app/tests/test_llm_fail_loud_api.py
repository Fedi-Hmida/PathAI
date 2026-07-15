"""P2 fail-loud contract at the API boundary.

With an enabled LLM agent whose provider always errors and the default
fail-loud fallback mode, the live user flows must return an explicit HTTP 503
`generation_unavailable` — never another topic's canned deterministic (RAG)
content. Fully offline: LLM_PROVIDER=fake, no network/credentials/DB.
"""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import app.agents.llm.client_selection as client_selection
from app.api.v1.dependencies import reset_api_container_for_tests
from app.core.settings import get_settings
from app.llm.fake_client import FakeLLMClient, FakeLLMScenario
from app.main import create_app


@pytest.fixture
def auth_enabled_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[pytest.MonkeyPatch]:
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "fail-loud-api-test-secret-value-0123456789")
    monkeypatch.setenv("REFRESH_COOKIE_SECURE", "false")
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    # Do NOT set PATHAI_LLM_FALLBACK_MODE — fail-loud is the default under test.
    get_settings.cache_clear()
    reset_api_container_for_tests()
    yield monkeypatch
    get_settings.cache_clear()


def _force_erroring_llm_client(monkeypatch: pytest.MonkeyPatch) -> None:
    # build_llm_client_for_agent() constructs FakeLLMClient() with no args for
    # the "fake" provider; swap in one whose every call raises a provider error
    # so the enabled LLM agent's generation always fails.
    monkeypatch.setattr(
        client_selection,
        "FakeLLMClient",
        lambda: FakeLLMClient(scenario=FakeLLMScenario.PROVIDER_ERROR),
    )


def _apply(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    reset_api_container_for_tests()


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "correcthorsebattery"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]  # type: ignore[no-any-return]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_workspace(client: TestClient, token: str, goal_text: str = "Learn NLP") -> str:
    response = client.post(
        "/api/v1/me/workspace",
        headers=_auth_header(token),
        json={"goal_text": goal_text},
    )
    assert response.status_code == 201
    return response.json()["run_id"]  # type: ignore[no-any-return]


def _assert_generation_unavailable(response, body_text: str) -> None:
    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "generation_unavailable"
    assert "retry" in body["detail"].lower()
    # No cross-topic RAG/demo content, and no leaked provider/secret detail.
    lowered = body_text.lower()
    for forbidden in ("rag", "retrieval", "question_", "fake", "provider"):
        assert forbidden not in lowered


def test_assessment_start_fails_loud_with_503_when_llm_errors(
    auth_enabled_env: pytest.MonkeyPatch,
) -> None:
    monkeypatch = auth_enabled_env
    monkeypatch.setenv("PATHAI_ENABLE_LLM_ASSESSMENT_AGENT", "true")
    _force_erroring_llm_client(monkeypatch)
    _apply(monkeypatch)

    client = TestClient(create_app(), raise_server_exceptions=False)
    token = _register(client, "learner@example.com")
    _create_workspace(client, token)

    response = client.post("/api/v1/me/assessment/start", headers=_auth_header(token))

    _assert_generation_unavailable(response, response.text)


def test_workspace_generate_fails_loud_with_503_when_llm_errors(
    auth_enabled_env: pytest.MonkeyPatch,
) -> None:
    monkeypatch = auth_enabled_env
    # Only the knowledge-map LLM agent is enabled: the diagnostic runs the
    # deterministic path (no LLM client), so the assessment completes and we
    # reach /generate, which then fails loud on the erroring LLM client.
    monkeypatch.setenv("PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT", "true")
    _force_erroring_llm_client(monkeypatch)
    _apply(monkeypatch)

    client = TestClient(create_app(), raise_server_exceptions=False)
    token = _register(client, "learner@example.com")
    _create_workspace(client, token)

    start = client.post("/api/v1/me/assessment/start", headers=_auth_header(token))
    assert start.status_code == 201
    assessment_id = start.json()["assessment_session_id"]
    question_id = start.json()["current_question"]["question_id"]
    for _ in range(5):
        answer = client.post(
            f"/api/v1/me/assessment/{assessment_id}/answer",
            headers=_auth_header(token),
            json={"question_id": question_id, "selected_options": [], "self_rating": 3},
        )
        assert answer.status_code == 200
        next_question = answer.json()["session"]["current_question"]
        if next_question is not None:
            question_id = next_question["question_id"]

    response = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))

    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "generation_unavailable"
    assert "retry" in body["detail"].lower()
    # The failed generation must NOT have silently persisted RAG content: the
    # error body carries none, and no provider/secret detail leaks.
    lowered = response.text.lower()
    for forbidden in ("fake", "provider"):
        assert forbidden not in lowered
