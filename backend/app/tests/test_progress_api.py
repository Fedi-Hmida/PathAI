from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.progress import progress_service
from app.db.mongodb import database_manager
from app.main import app


def test_progress_api_initialize_update_and_fetch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())
    progress_service.store.clear()

    with TestClient(app) as client:
        curriculum_response = client.get("/api/v1/dev/curriculum/example")
        curriculum = curriculum_response.json()["result"]["curriculum"]

        initialize = client.post(
            "/api/v1/progress/initialize",
            json={"curriculum": curriculum},
        )
        assert initialize.status_code == 200
        summary = initialize.json()["summary"]
        first_topic = summary["weeks"][0]["topics"][0]

        update = client.post(
            "/api/v1/progress/update",
            json={
                "curriculum_id": summary["curriculum_id"],
                "week_number": 1,
                "topic_id": first_topic["topic_id"],
                "status": "done",
            },
        )
        assert update.status_code == 200
        assert update.json()["event"]["event"] == "marked_done"

        fetched = client.get(f"/api/v1/progress/{summary['curriculum_id']}")
        assert fetched.status_code == 200
        assert fetched.json()["analytics"]["completed_topic_count"] == 1

        week = client.get(f"/api/v1/progress/{summary['curriculum_id']}/week/1")
        assert week.status_code == 200
        assert week.json()["week"]["week_number"] == 1


def test_dev_progress_example_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.get("/api/v1/dev/progress/example")

        assert response.status_code == 200
        assert response.json()["summary"]["analytics"]["completed_topic_count"] == 1
