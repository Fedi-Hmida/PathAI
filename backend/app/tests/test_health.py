from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.db.mongodb import database_manager
from app.main import app


def test_health_check(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["service"] == "PathAI API"


def test_readiness_check_database_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())
    monkeypatch.setattr(database_manager, "ready", AsyncMock(return_value=True))

    with TestClient(app) as client:
        response = client.get("/api/v1/ready")

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ready"
        assert payload["checks"]["mongodb"] == "ok"


def test_readiness_check_database_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())
    monkeypatch.setattr(database_manager, "ready", AsyncMock(return_value=False))
    database_manager.last_error = "mocked database unavailable"

    with TestClient(app) as client:
        response = client.get("/api/v1/ready")

        assert response.status_code == 503
        payload = response.json()
        assert payload["status"] == "not_ready"
        assert payload["checks"]["mongodb"] == "unavailable"
        assert payload["message"] == "mocked database unavailable"


def test_readiness_check_redacts_mongodb_uri(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())
    monkeypatch.setattr(database_manager, "ready", AsyncMock(return_value=False))
    database_manager.last_error = "failed for mongodb+srv://user:secret@example.test/pathai"

    with TestClient(app) as client:
        response = client.get("/api/v1/ready")

        assert response.status_code == 503
        payload = response.json()
        assert payload["message"] == "failed for [REDACTED_SECRET]"
        assert "secret" not in payload["message"]
