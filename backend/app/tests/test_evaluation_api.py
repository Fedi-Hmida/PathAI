from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.db.mongodb import database_manager
from app.main import app


def test_evaluation_api_endpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        datasets = client.get("/api/v1/evaluation/datasets")
        assert datasets.status_code == 200
        assert datasets.json()["datasets"][0]["fixture_count"] >= 5

        report = client.post("/api/v1/evaluation/run-sample", json={})
        assert report.status_code == 200
        payload = report.json()
        assert payload["system_variant"] == "pathai_full"
        assert payload["baseline_comparisons"]
        assert "synthetic" in " ".join(payload["limitations"]).lower()

        learning_gain = client.post(
            "/api/v1/evaluation/learning-gain",
            json={"pre_test_score": 40, "post_test_score": 70, "max_score": 100},
        )
        assert learning_gain.status_code == 200
        assert learning_gain.json()["normalized_learning_gain"] == 0.5

        rubrics = client.get("/api/v1/evaluation/rubrics")
        assert rubrics.status_code == 200
        assert len(rubrics.json()["rubrics"]) >= 4


def test_dev_evaluation_example_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.get("/api/v1/dev/evaluation/example")

        assert response.status_code == 200
        assert response.json()["metric_scores"]
