from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.v1.dependencies import reset_api_container_for_tests
from app.fixtures import canonical_demo as demo
from app.main import create_app


def test_demo_load_fixtures_returns_deterministic_key_ids() -> None:
    client = _client()

    first_response = client.post("/api/v1/demo/load-fixtures")
    second_response = client.post("/api/v1/demo/load-fixtures")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_body = first_response.json()
    second_body = second_response.json()
    assert first_body["deterministic"] is True
    assert first_body["mode"] == "demo"
    assert first_body["run_id"] == demo.RUN_ID
    assert first_body["goal_id"] == demo.GOAL_ID
    assert first_body["assessment_id"] == demo.ASSESSMENT_ID
    assert first_body["knowledge_map_id"] == demo.KNOWLEDGE_MAP_ID
    assert first_body["curriculum_id"] == demo.CURRICULUM_ID
    assert first_body["progress_id"] == demo.PROGRESS_ID
    assert first_body["quiz_id"] == demo.QUIZ_ID
    assert first_body["quiz_attempt_id"] == demo.QUIZ_ATTEMPT_ID
    assert first_body["adaptation_id"] == demo.ADAPTATION_ID
    assert first_body["critic_id"] == demo.CRITIC_REVIEW_ID
    assert first_body["evaluation_id"] == demo.EVALUATION_REPORT_ID
    assert first_body["dashboard_payload"]["run_summary"]["run_id"] == demo.RUN_ID
    assert first_body == second_body


def test_demo_load_fixtures_clears_existing_fake_store_state() -> None:
    client = _client()
    create_response = client.post(
        "/api/v1/goals",
        json={"goal_text": "Learn API contract testing for a semester project"},
    )
    created_goal_id = create_response.json()["goal_id"]

    load_response = client.post("/api/v1/demo/load-fixtures")
    stale_goal_response = client.get(f"/api/v1/goals/{created_goal_id}")
    demo_goal_response = client.get(f"/api/v1/goals/{demo.GOAL_ID}")

    assert load_response.status_code == 200
    assert stale_goal_response.status_code == 404
    assert demo_goal_response.status_code == 200


def _client() -> TestClient:
    reset_api_container_for_tests()
    return TestClient(create_app())
