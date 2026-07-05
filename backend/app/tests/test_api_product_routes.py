from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.v1.dependencies import reset_api_container_for_tests
from app.fixtures import canonical_demo as demo
from app.main import create_app


def test_health_and_product_routes_return_fixture_backed_payloads() -> None:
    client = _client()

    assert client.get("/api/v1/health").status_code == 200
    _load_demo(client)

    cases = [
        (f"/api/v1/goals/{demo.GOAL_ID}", "goal_id", demo.GOAL_ID),
        (
            f"/api/v1/assessments/{demo.ASSESSMENT_ID}",
            "assessment_session_id",
            demo.ASSESSMENT_ID,
        ),
        (
            f"/api/v1/knowledge-maps/{demo.KNOWLEDGE_MAP_ID}",
            "knowledge_map_id",
            demo.KNOWLEDGE_MAP_ID,
        ),
        (f"/api/v1/curricula/{demo.CURRICULUM_ID}", "curriculum_id", demo.CURRICULUM_ID),
        (
            f"/api/v1/resources/{demo.RESOURCE_CORPUS[0].resource_id}",
            "resource_id",
            demo.RESOURCE_CORPUS[0].resource_id,
        ),
        (f"/api/v1/progress/{demo.PROGRESS_ID}", "progress_state_id", demo.PROGRESS_ID),
        (f"/api/v1/adaptations/{demo.ADAPTATION_ID}", "adaptation_event_id", demo.ADAPTATION_ID),
        (
            f"/api/v1/critic-reviews/{demo.CRITIC_REVIEW_ID}",
            "critic_review_id",
            demo.CRITIC_REVIEW_ID,
        ),
        (
            f"/api/v1/evaluations/{demo.EVALUATION_REPORT_ID}",
            "evaluation_report_id",
            demo.EVALUATION_REPORT_ID,
        ),
        (f"/api/v1/orchestration/runs/{demo.RUN_ID}", "run_id", demo.RUN_ID),
    ]

    for path, id_field, expected_id in cases:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()[id_field] == expected_id


def test_resources_by_curriculum_returns_resource_attachments() -> None:
    client = _client()
    _load_demo(client)

    response = client.get(f"/api/v1/resources/by-curriculum/{demo.CURRICULUM_ID}")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == len(demo.RESOURCE_ATTACHMENTS)
    assert body[0]["curriculum_id"] == demo.CURRICULUM_ID


def test_quiz_endpoint_returns_learner_safe_quiz_without_answer_keys() -> None:
    client = _client()
    _load_demo(client)

    response = client.get(f"/api/v1/quizzes/{demo.QUIZ_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["quiz_id"] == demo.QUIZ_ID
    assert "correct_answer" not in body["questions"][0]
    assert "explanation" not in body["questions"][0]


def test_goal_create_endpoint_creates_no_auth_local_goal_only() -> None:
    client = _client()

    response = client.post(
        "/api/v1/goals",
        json={"goal_text": "Learn reliable prompt evaluation for a class project"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["goal_id"].startswith("goal_")
    assert body["run_id"].startswith("run_")
    assert body["status"] == "created"
    assert body["goal_text"] == "Learn reliable prompt evaluation for a class project"


def _client() -> TestClient:
    reset_api_container_for_tests()
    return TestClient(create_app())


def _load_demo(client: TestClient) -> None:
    response = client.post("/api/v1/demo/load-fixtures")
    assert response.status_code == 200
