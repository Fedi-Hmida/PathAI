from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.assessment import assessment_service
from app.db.mongodb import database_manager
from app.main import app


def test_assessment_api_start_get_answer_finalize(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())
    assessment_service.store.clear()

    with TestClient(app) as client:
        start_response = client.post(
            "/api/v1/assessment/start",
            json={
                "goal": "Learn RAG systems",
                "timeline_weeks": 8,
                "hours_per_week": 10,
                "target_level": "intermediate",
                "max_questions": 3,
            },
        )
        assert start_response.status_code == 200
        started = start_response.json()
        session_id = started["session"]["session_id"]
        assert started["next_question"]["source"] == "mock_llm"

        get_response = client.get(f"/api/v1/assessment/{session_id}")
        assert get_response.status_code == 200
        assert get_response.json()["session"]["session_id"] == session_id

        answer_response = client.post(
            f"/api/v1/assessment/{session_id}/answer",
            json={"answer": "Embedding is a vector representation for semantic similarity."},
        )
        assert answer_response.status_code == 200
        assert answer_response.json()["evaluation"]["signal"] == "strong"

        finalize_response = client.post(f"/api/v1/assessment/{session_id}/finalize")
        assert finalize_response.status_code == 200
        payload = finalize_response.json()
        assert payload["result"]["status"] == "completed"
        assert payload["result"]["knowledge_map"]["confidence_score"] > 0


def test_assessment_api_missing_session_returns_structured_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.get("/api/v1/assessment/missing-session")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "assessment_session_not_found"
