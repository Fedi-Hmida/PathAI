from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.assessment import assessment_service
from app.api.v1.curriculum import curriculum_service
from app.db.mongodb import database_manager
from app.main import app


def test_curriculum_api_generate_get_and_validate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())
    curriculum_service.store.clear()

    payload = {
        "goal": "Learn RAG systems",
        "timeline_weeks": 4,
        "hours_per_week": 6,
        "knowledge_map": {
            "strong": ["Python basics"],
            "weak": ["Embeddings"],
            "missing": ["Chunking", "Reranking"],
            "recommended_level": "beginner",
            "confidence_score": 0.84,
            "assessment_notes": ["API test map."],
        },
    }

    with TestClient(app) as client:
        validate_response = client.post("/api/v1/curriculum/validate", json=payload)
        assert validate_response.status_code == 200
        assert validate_response.json()["valid"] is True

        generate_response = client.post("/api/v1/curriculum/generate", json=payload)
        assert generate_response.status_code == 200
        generated = generate_response.json()["result"]["curriculum"]
        curriculum_id = generated["curriculum_id"]
        assert generated["source"] == "mock_llm"
        assert len(generated["weeks"]) == 4

        get_response = client.get(f"/api/v1/curriculum/{curriculum_id}")
        assert get_response.status_code == 200
        assert get_response.json()["curriculum"]["curriculum_id"] == curriculum_id


def test_curriculum_api_generates_from_completed_assessment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())
    assessment_service.store.clear()
    curriculum_service.store.clear()

    with TestClient(app) as client:
        start = client.post(
            "/api/v1/assessment/start",
            json={
                "goal": "Learn RAG systems",
                "timeline_weeks": 4,
                "hours_per_week": 6,
                "target_level": "beginner",
                "max_questions": 3,
            },
        )
        session_id = start.json()["session"]["session_id"]
        client.post(
            f"/api/v1/assessment/{session_id}/answer",
            json={"answer": "A vector representation for semantic similarity."},
        )
        client.post(f"/api/v1/assessment/{session_id}/finalize")

        curriculum_response = client.post(
            "/api/v1/curriculum/generate",
            json={"assessment_session_id": session_id},
        )

        assert curriculum_response.status_code == 200
        curriculum = curriculum_response.json()["result"]["curriculum"]
        assert curriculum["assessment_session_id"] == session_id
        assert curriculum["goal"] == "Learn RAG systems"
        assert curriculum["weeks"][-1]["project_or_application"] is True


def test_curriculum_api_rejects_incomplete_assessment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())
    assessment_service.store.clear()

    with TestClient(app) as client:
        start = client.post(
            "/api/v1/assessment/start",
            json={
                "goal": "Learn RAG systems",
                "timeline_weeks": 4,
                "hours_per_week": 6,
                "target_level": "beginner",
            },
        )
        session_id = start.json()["session"]["session_id"]

        response = client.post(
            "/api/v1/curriculum/generate",
            json={"assessment_session_id": session_id},
        )

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "assessment_not_ready_for_curriculum"


def test_dev_curriculum_example_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.get("/api/v1/dev/curriculum/example")

        assert response.status_code == 200
        payload = response.json()
        assert payload["result"]["curriculum"]["weeks"]
        assert payload["result"]["curriculum"]["source"] == "mock_llm"
