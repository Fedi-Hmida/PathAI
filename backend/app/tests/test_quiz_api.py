from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.quiz import quiz_service
from app.db.mongodb import database_manager
from app.main import app


def test_quiz_api_generate_get_submit_and_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())
    quiz_service.store.clear()

    with TestClient(app) as client:
        curriculum = client.get("/api/v1/dev/curriculum/example").json()["result"][
            "curriculum"
        ]

        generated = client.post(
            "/api/v1/quiz/generate",
            json={
                "curriculum": curriculum,
                "week_number": 1,
                "question_count": 5,
            },
        )
        assert generated.status_code == 200
        quiz = generated.json()["quiz"]
        quiz_id = quiz["quiz_id"]

        fetched = client.get(f"/api/v1/quiz/{quiz_id}")
        assert fetched.status_code == 200
        assert fetched.json()["quiz_id"] == quiz_id

        submitted = client.post(
            f"/api/v1/quiz/{quiz_id}/submit",
            json={
                "answers": [
                    {
                        "question_id": question["question_id"],
                        "answer": question["correct_answer"],
                    }
                    for question in quiz["questions"]
                ]
            },
        )
        assert submitted.status_code == 200
        assert submitted.json()["score"] == 1.0

        history = client.get(f"/api/v1/quiz/{quiz['curriculum_id']}/history")
        assert history.status_code == 200
        assert history.json()["best_score"] == 1.0


def test_dev_quiz_example_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.get("/api/v1/dev/quiz/example")

        assert response.status_code == 200
        assert response.json()["result"]["score"] == 1.0
