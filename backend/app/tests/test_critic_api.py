from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.db.mongodb import database_manager
from app.main import app


def test_critic_rubric_review_and_dev_example_endpoints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        rubric = client.get("/api/v1/critic/rubric")
        assert rubric.status_code == 200
        assert rubric.json()["approval_threshold"] >= 0.7

        curriculum_response = client.get("/api/v1/dev/curriculum/example")
        assert curriculum_response.status_code == 200
        curriculum = curriculum_response.json()["result"]["curriculum"]

        curriculum_review = client.post(
            "/api/v1/critic/review-curriculum",
            json={"curriculum": curriculum},
        )
        assert curriculum_review.status_code == 200
        assert curriculum_review.json()["decision"] in {"approved", "rejected", "auto_approved"}
        assert curriculum_review.json()["resource_coverage_review"]["resources_reviewed"] is False

        resource_response = client.post(
            "/api/v1/resources/retrieve-for-curriculum",
            json={"curriculum": curriculum, "top_k": 2},
        )
        assert resource_response.status_code == 200

        critic_response = client.post(
            "/api/v1/critic/review",
            json={
                "curriculum": curriculum,
                "resource_attachment": resource_response.json(),
                "required_resources_per_topic": 1,
            },
        )
        assert critic_response.status_code == 200
        assert critic_response.json()["decision"] in {"approved", "rejected", "auto_approved"}

        example = client.get("/api/v1/dev/critic/example")
        assert example.status_code == 200
        assert "review" in example.json()
