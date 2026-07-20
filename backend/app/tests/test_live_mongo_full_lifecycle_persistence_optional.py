from __future__ import annotations

import os
import re
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.v1.dependencies import ApiServiceContainer, get_api_container
from app.core.settings import Settings, get_settings
from app.main import create_app

ENABLE_LIVE_MONGO_TESTS = "ENABLE_LIVE_MONGO_TESTS"

pytestmark = pytest.mark.skipif(
    os.getenv(ENABLE_LIVE_MONGO_TESTS, "").lower() not in {"1", "true", "yes"},
    reason=(
        "Live MongoDB checks are optional and require "
        f"{ENABLE_LIVE_MONGO_TESTS}=1."
    ),
)

# Same pattern as test_assessment_behavior.py / test_knowledge_map_behavior.py /
# test_quiz_behavior.py -- reused verbatim, not a new detector (provenance-audit
# finding P7).
_RAG_TOKEN_PATTERN = re.compile(
    r"\b(rag|retrieval|reranking|chunking|embeddings?|vector[_ ]search|hallucination)\b",
    re.IGNORECASE,
)

_GOAL_TEXT = "Learn functional programming with Haskell for a new job"


@pytest.fixture
def _mongo_backend_and_auth_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    if not Settings().mongodb_uri:
        pytest.skip("MONGODB_URI is not configured.")
    monkeypatch.setenv("REPOSITORY_BACKEND", "mongo")
    monkeypatch.setenv("PATHAI_ENABLE_AUTH", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "live-mongo-lifecycle-test-secret-0123456789")
    monkeypatch.setenv("REFRESH_COOKIE_SECURE", "false")
    get_settings.cache_clear()
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


def _complete_assessment(client: TestClient, token: str) -> None:
    start = client.post("/api/v1/me/assessment/start", headers=_auth_header(token))
    assert start.status_code == 201
    assessment_id = start.json()["assessment_session_id"]
    question_id = start.json()["current_question"]["question_id"]
    for _ in range(10):
        response = client.post(
            f"/api/v1/me/assessment/{assessment_id}/answer",
            headers=_auth_header(token),
            json={"question_id": question_id, "selected_options": [], "self_rating": 3},
        )
        assert response.status_code == 200
        next_question = response.json()["session"]["current_question"]
        if next_question is None:
            return
        question_id = next_question["question_id"]


@pytest.mark.live_mongo
def test_full_lifecycle_persists_to_mongo_survives_fresh_container_no_rag_leak(
    _mongo_backend_and_auth_env: None,
) -> None:
    writer_container = ApiServiceContainer()
    app = create_app()
    app.dependency_overrides[get_api_container] = lambda: writer_container
    client = TestClient(app)

    try:
        token = _register(client, "live-mongo-lifecycle-test@example.com")
        create_ws = client.post(
            "/api/v1/me/workspace",
            headers=_auth_header(token),
            json={"goal_text": _GOAL_TEXT},
        )
        assert create_ws.status_code == 201
        run_id = create_ws.json()["run_id"]

        _complete_assessment(client, token)

        generate = client.post("/api/v1/me/workspace/generate", headers=_auth_header(token))
        assert generate.status_code == 200
        artifact_ids = generate.json()

        # Provenance-audit finding P7: zero RAG-demo vocabulary leaks into a
        # topic-general (non-RAG) goal's real, freshly generated content.
        dashboard = client.get(f"/api/v1/dashboard/{run_id}", headers=_auth_header(token))
        assert dashboard.status_code == 200
        haystack = " ".join(
            str(value) for value in _flatten(dashboard.json())
        )
        assert not _RAG_TOKEN_PATTERN.search(haystack), haystack

        # A second, independently constructed container -- the same
        # "reader" pattern test_live_mongo_api_container_end_to_end_optional.py
        # and test_live_mongo_orchestration_run_route_optional.py already use
        # to prove data survives beyond the writer's own process/connection,
        # standing in for a genuine process restart.
        reader_container = ApiServiceContainer()
        goal = reader_container.goal_service.get_by_id(
            dashboard.json()["goal_summary"]["goal_id"],
        )
        assert goal.run_id == run_id

        knowledge_map = reader_container.knowledge_map_service.get_by_id(
            artifact_ids["knowledge_map_id"],
        )
        curriculum = reader_container.curriculum_service.get_by_id(
            artifact_ids["curriculum_id"],
        )
        critic_review = reader_container.critic_service.get_by_id(
            artifact_ids["critic_review_id"],
        )
        quiz = reader_container.quiz_service.get_quiz_by_id(artifact_ids["quiz_id"])

        reread_haystack = " ".join(
            str(value)
            for value in (
                *_flatten(knowledge_map.model_dump(mode="json")),
                *_flatten(curriculum.model_dump(mode="json")),
                *_flatten(critic_review.model_dump(mode="json")),
                *_flatten(quiz.model_dump(mode="json")),
            )
        )
        assert not _RAG_TOKEN_PATTERN.search(reread_haystack), reread_haystack
    finally:
        writer_container.clear()


def _flatten(value: object) -> Iterator[object]:
    """Yield every leaf value in a nested dict/list, for a haystack-style scan."""
    if isinstance(value, dict):
        for item in value.values():
            yield from _flatten(item)
    elif isinstance(value, list):
        for item in value:
            yield from _flatten(item)
    else:
        yield value
