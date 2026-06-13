from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.db.mongodb import database_manager
from app.main import app


def test_resource_catalog_retrieve_validate_and_dev_example(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        summary = client.get("/api/v1/resources/catalog/summary")
        assert summary.status_code == 200
        assert summary.json()["total_resources"] >= 4

        retrieval = client.post(
            "/api/v1/resources/retrieve",
            json={
                "topic": "Chunking",
                "goal": "Learn RAG systems",
                "difficulty": "beginner",
                "subtopics": ["text splitting"],
                "top_k": 2,
            },
        )
        assert retrieval.status_code == 200
        assert retrieval.json()["candidates"][0]["resource"]["title"].startswith("LlamaIndex")

        seed = {
            "title": "API Seed",
            "url": "https://example.com/pathai/api-seed",
            "type": "article",
            "topics": ["API"],
            "subtopics": [],
            "difficulty": "beginner",
            "estimated_time_minutes": 10,
            "source": "Example",
            "quality_score": 0.7,
            "access_label": "open",
            "foundational": False,
            "last_verified": "2026-06-09",
        }
        validation = client.post("/api/v1/resources/validate-seed", json=seed)
        assert validation.status_code == 200
        assert validation.json()["mapped_resource"]["source_domain"] == "example.com"

        example = client.get("/api/v1/dev/resources/example")
        assert example.status_code == 200
        assert example.json()["retrieval"]["candidates"]


def test_resource_attachment_endpoint_enriches_curriculum(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        curriculum_response = client.get("/api/v1/dev/curriculum/example")
        assert curriculum_response.status_code == 200
        curriculum = curriculum_response.json()["result"]["curriculum"]

        response = client.post(
            "/api/v1/resources/retrieve-for-curriculum",
            json={"curriculum": curriculum, "top_k": 2},
        )

        assert response.status_code == 200
        payload = response.json()
        first_topic = payload["enriched_curriculum"]["weeks"][0]["topics"][0]
        assert "resources" in first_topic
        assert first_topic["resources"]
        assert payload["topic_results"]
