from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.v1.dependencies import reset_api_container_for_tests
from app.fixtures import canonical_demo as demo
from app.main import create_app
from app.schemas.dashboard import DashboardPayload
from app.schemas.orchestration import OrchestrationStatusResponse


def test_dashboard_endpoint_returns_dashboard_payload() -> None:
    client = _client()
    _load_demo(client)

    response = client.get(f"/api/v1/dashboard/{demo.RUN_ID}")

    assert response.status_code == 200
    payload = DashboardPayload.model_validate(response.json())
    assert payload.run_summary.run_id == demo.RUN_ID
    assert payload.goal_summary.goal_id == demo.GOAL_ID
    assert payload.resources_summary is not None
    assert payload.resources_summary.total_attached == len(demo.RESOURCE_ATTACHMENTS)


def test_orchestration_status_endpoint_returns_lightweight_status_payload() -> None:
    client = _client()
    _load_demo(client)

    response = client.get(f"/api/v1/orchestration/runs/{demo.RUN_ID}/status")

    assert response.status_code == 200
    payload = OrchestrationStatusResponse.model_validate(response.json())
    assert payload.run_id == demo.RUN_ID
    assert payload.status == "completed"
    assert payload.requires_user_input is False


def _client() -> TestClient:
    reset_api_container_for_tests()
    return TestClient(create_app())


def _load_demo(client: TestClient) -> None:
    response = client.post("/api/v1/demo/load-fixtures")
    assert response.status_code == 200
