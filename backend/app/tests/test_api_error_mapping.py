from __future__ import annotations

from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.dependencies import get_goal_service, reset_api_container_for_tests
from app.main import create_app
from app.repositories.errors import DuplicateRecordError
from app.schemas.goal import LearningGoalDTO


class DuplicateGoalService:
    def create(self, _goal: LearningGoalDTO) -> LearningGoalDTO:
        msg = "duplicate goal for test"
        raise DuplicateRecordError(msg)


def test_missing_api_resource_returns_404() -> None:
    client = _client()

    response = client.get("/api/v1/goals/goal_missing_demo")

    assert response.status_code == 404
    assert response.json() == {"detail": "resource not found"}


def test_duplicate_repository_error_returns_409() -> None:
    client = _client()
    app = cast(FastAPI, client.app)
    app.dependency_overrides[get_goal_service] = lambda: DuplicateGoalService()

    response = client.post(
        "/api/v1/goals",
        json={"goal_text": "Learn clean API boundaries for a project"},
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "resource already exists"}


def test_malformed_create_goal_request_returns_422() -> None:
    client = _client()

    response = client.post("/api/v1/goals", json={"goal_text": "bad"})

    assert response.status_code == 422


def _client() -> TestClient:
    reset_api_container_for_tests()
    return TestClient(create_app())
