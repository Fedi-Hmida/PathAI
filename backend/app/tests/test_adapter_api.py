from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.adapt import adapter_service
from app.db.mongodb import database_manager
from app.main import app


def test_adapt_api_check_replan_get_and_history(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())
    adapter_service.store.clear()

    with TestClient(app) as client:
        curriculum = client.get("/api/v1/dev/curriculum/example").json()["result"][
            "curriculum"
        ]
        resource_attachment = client.post(
            "/api/v1/resources/retrieve-for-curriculum",
            json={"curriculum": curriculum, "top_k": 2},
        ).json()
        progress = client.post(
            "/api/v1/progress/initialize",
            json={"curriculum": curriculum},
        ).json()["summary"]
        first_topic = progress["weeks"][0]["topics"][0]
        progress = client.post(
            "/api/v1/progress/update",
            json={
                "curriculum_id": progress["curriculum_id"],
                "week_number": 1,
                "topic_id": first_topic["topic_id"],
                "status": "stuck",
            },
        ).json()["summary"]

        check = client.post(
            "/api/v1/adapt/check",
            json={
                "curriculum": curriculum,
                "progress_summary": progress,
                "expected_week_number": 1,
            },
        )
        assert check.status_code == 200
        assert check.json()["should_replan"] is True

        replan = client.post(
            "/api/v1/adapt/replan",
            json={
                "curriculum": curriculum,
                "progress_summary": progress,
                "expected_week_number": 1,
                "existing_resource_attachment": resource_attachment,
            },
        )
        assert replan.status_code == 200
        payload = replan.json()
        assert payload["decision"]["decision"] == "replanned"
        adaptation_id = payload["adaptation_id"]

        fetched = client.get(f"/api/v1/adapt/{adaptation_id}")
        assert fetched.status_code == 200
        assert fetched.json()["adaptation_id"] == adaptation_id

        history = client.get(f"/api/v1/adapt/{curriculum['curriculum_id']}/history")
        assert history.status_code == 200
        assert len(history.json()["adaptations"]) == 1


def test_dev_adapt_example_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.get("/api/v1/dev/adapt/example")

        assert response.status_code == 200
        assert response.json()["result"]["decision"]["should_replan"] is True
