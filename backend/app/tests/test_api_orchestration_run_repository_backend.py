from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_api_container, reset_api_container_for_tests
from app.fixtures import canonical_demo as demo
from app.main import create_app
from app.repositories.fakes import FakeGoalRepository, FakeOrchestrationRunRepository


def test_route_uses_fake_repositories_by_default_and_persists_the_run() -> None:
    reset_api_container_for_tests()
    container = get_api_container()
    assert isinstance(container.goal_repository, FakeGoalRepository)
    assert isinstance(container.orchestration_run_repository, FakeOrchestrationRunRepository)

    client = TestClient(create_app())
    response = client.post("/api/v1/orchestration/runs")

    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    get_response = client.get(f"/api/v1/orchestration/runs/{demo.RUN_ID}")
    assert get_response.status_code == 200
    assert get_response.json()["goal_id"] == demo.GOAL_ID
