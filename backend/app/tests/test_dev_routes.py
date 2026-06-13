from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.db.mongodb import database_manager
from app.main import app


def test_dev_models_lists_registered_documents(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.get("/api/v1/dev/models")

        assert response.status_code == 200
        payload = response.json()
        assert "UserProfileDocument" in payload["models"]
        assert "ResourceDocument" in payload["models"]
        assert "ProgressLogDocument" in payload["models"]


def test_dev_goal_validation_does_not_persist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    request_body = {
        "title": "  Learn RAG systems  ",
        "description": "Build a graduation project with retrieval and evaluation.",
        "target_level": "intermediate",
        "timeline_weeks": 8,
        "hours_per_week": 10,
    }

    with TestClient(app) as client:
        response = client.post("/api/v1/dev/goals/validate", json=request_body)

        assert response.status_code == 200
        payload = response.json()
        assert payload["valid"] is True
        assert payload["goal"]["title"] == "Learn RAG systems"
        assert "No data was persisted" in payload["message"]


def test_dev_llm_config_does_not_expose_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.get("/api/v1/dev/llm/config")

        assert response.status_code == 200
        payload = response.json()
        assert "api_key" not in payload
        assert payload["mock_mode"] is True


def test_dev_llm_mock_structured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/dev/llm/mock-structured",
            json={"context": "Phase 2 endpoint test"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert "Mock LLM structured output validated" in payload["message"]


def test_dev_real_llm_health_check_blocked_in_mock_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.post("/api/v1/dev/llm/health-check")

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "llm_not_configured"
