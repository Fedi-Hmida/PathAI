from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.db.mongodb import database_manager
from app.main import app


def test_dev_graph_definition_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.get("/api/v1/dev/graph/definition")

        assert response.status_code == 200
        payload = response.json()
        assert "critic_node" in payload["nodes"]
        assert payload["real_llm_calls"] is False
        assert payload["database_writes"] is False


def test_dev_graph_demo_run_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/dev/graph/demo-run",
            json={
                "goal": "Learn LangGraph routing",
                "critic_reject_until_revision": 1,
                "max_revisions": 2,
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["final_state"]["job_status"] == "completed"
        assert payload["final_state"]["revision_count"] == 1
        assert any(event["node_name"] == "resource_node" for event in payload["trace"])


def test_dev_graph_demo_failure_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/dev/graph/demo-run",
            json={"simulate_failure_node": "resource_node"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["final_state"]["job_status"] == "failed"
        assert payload["errors"][0]["code"] == "simulated_node_failure"
