from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.v1.dependencies import reset_api_container_for_tests
from app.fixtures import canonical_demo as demo
from app.main import create_app


def test_sequential_double_post_converges_to_completed_with_no_duplicate_key_error() -> None:
    # A no-auth local demo has no run-identity concept beyond the fixed demo
    # RUN_ID/GOAL_ID (decision 3 of the Rebuild-18 plan). Hitting the route
    # twice in a row must not surface a raw DuplicateRecordError/500 -- every
    # node already uses create-or-get / re-save semantics for exactly this
    # reason (initialize_run resets an existing IN_PROGRESS row rather than
    # failing on the second call).
    client = _client()

    first_response = client.post("/api/v1/orchestration/runs")
    second_response = client.post("/api/v1/orchestration/runs")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_body = first_response.json()
    second_body = second_response.json()
    assert first_body["status"] == "completed"
    assert second_body["status"] == "completed"
    assert first_body["run_id"] == second_body["run_id"] == demo.RUN_ID
    assert second_body["failed_nodes"] == []


def test_three_sequential_posts_all_succeed() -> None:
    client = _client()

    responses = [client.post("/api/v1/orchestration/runs") for _ in range(3)]

    for response in responses:
        assert response.status_code == 200
        assert response.json()["status"] == "completed"


def _client() -> TestClient:
    reset_api_container_for_tests()
    return TestClient(create_app())
