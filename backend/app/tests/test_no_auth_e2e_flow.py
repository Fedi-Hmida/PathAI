from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.adapt import adapter_service
from app.api.v1.assessment import assessment_service
from app.api.v1.curriculum import curriculum_service
from app.api.v1.progress import progress_service
from app.api.v1.quiz import quiz_service
from app.db.mongodb import database_manager
from app.main import app


def test_full_no_auth_backend_flow(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    assessment_service.store.clear()
    curriculum_service.store.clear()
    progress_service.store.clear()
    quiz_service.store.clear()
    adapter_service.store.clear()

    with TestClient(app) as client:
        start = client.post(
            "/api/v1/assessment/start",
            json={
                "goal": "Learn RAG systems for AI engineering",
                "timeline_weeks": 4,
                "hours_per_week": 6,
                "target_level": "beginner",
                "max_questions": 3,
            },
        )
        assert start.status_code == 200
        session_id = start.json()["session"]["session_id"]

        answer = client.post(
            f"/api/v1/assessment/{session_id}/answer",
            json={
                "answer": "Embeddings represent text for semantic similarity search."
            },
        )
        assert answer.status_code == 200
        answer_payload = answer.json()
        assert answer_payload["evaluation"]["signal"] in {"strong", "weak", "missing"}

        finalized = client.post(f"/api/v1/assessment/{session_id}/finalize")
        assert finalized.status_code == 200
        finalized_payload = finalized.json()
        assert finalized_payload["result"]["knowledge_map"]["recommended_level"]

        curriculum_res = client.post(
            "/api/v1/curriculum/generate",
            json={"assessment_session_id": session_id},
        )
        assert curriculum_res.status_code == 200
        curriculum = curriculum_res.json()["result"]["curriculum"]
        curriculum_id = curriculum["curriculum_id"]
        assert len(curriculum["weeks"]) == 4

        resources = client.post(
            "/api/v1/resources/retrieve-for-curriculum",
            json={"curriculum": curriculum, "top_k": 2},
        )
        assert resources.status_code == 200
        resource_attachment = resources.json()
        assert resource_attachment["curriculum_id"] == curriculum_id
        assert resource_attachment["topic_results"]
        assert resource_attachment["attachments"]
        assert resource_attachment["attachments"][0]["resources"]

        critic = client.post(
            "/api/v1/critic/review",
            json={
                "curriculum": curriculum,
                "resource_attachment": resource_attachment,
                "required_resources_per_topic": 1,
                "revision_count": 0,
                "max_revisions": 2,
            },
        )
        assert critic.status_code == 200
        critic_payload = critic.json()
        assert critic_payload["decision"] in {
            "approved",
            "rejected",
            "auto_approved",
        }
        assert 0 <= critic_payload["overall_quality_score"] <= 1

        progress = client.post(
            "/api/v1/progress/initialize",
            json={"curriculum": curriculum},
        )
        assert progress.status_code == 200
        progress_summary = progress.json()["summary"]
        first_topic = progress_summary["weeks"][0]["topics"][0]

        progress_update = client.post(
            "/api/v1/progress/update",
            json={
                "curriculum_id": curriculum_id,
                "week_number": 1,
                "topic_id": first_topic["topic_id"],
                "status": "stuck",
            },
        )
        assert progress_update.status_code == 200
        progress_summary = progress_update.json()["summary"]
        assert progress_summary["analytics"]["stuck_topic_count"] >= 1

        quiz = client.post(
            "/api/v1/quiz/generate",
            json={
                "curriculum": curriculum,
                "week_number": 1,
                "resource_attachment": resource_attachment,
                "question_count": 3,
            },
        )
        assert quiz.status_code == 200
        quiz_payload = quiz.json()["quiz"]
        assert quiz_payload["curriculum_id"] == curriculum_id
        assert len(quiz_payload["questions"]) == 3

        submitted = client.post(
            f"/api/v1/quiz/{quiz_payload['quiz_id']}/submit",
            json={
                "answers": [
                    {
                        "question_id": question["question_id"],
                        "answer": question["correct_answer"],
                    }
                    for question in quiz_payload["questions"]
                ]
            },
        )
        assert submitted.status_code == 200
        assert submitted.json()["score"] == 1.0

        history = client.get(f"/api/v1/quiz/{curriculum_id}/history")
        assert history.status_code == 200
        quiz_history = history.json()
        assert len(quiz_history["attempts"]) == 1

        check = client.post(
            "/api/v1/adapt/check",
            json={
                "curriculum": curriculum,
                "progress_summary": progress_summary,
                "quiz_history": quiz_history,
                "expected_week_number": 1,
            },
        )
        assert check.status_code == 200
        assert check.json()["should_replan"] is True

        replan = client.post(
            "/api/v1/adapt/replan",
            json={
                "curriculum": curriculum,
                "progress_summary": progress_summary,
                "quiz_history": quiz_history,
                "expected_week_number": 1,
                "existing_resource_attachment": resource_attachment,
            },
        )
        assert replan.status_code == 200
        replan_payload = replan.json()
        assert replan_payload["decision"]["decision"] == "replanned"
        assert replan_payload["resource_attachment"] is not None
        assert replan_payload["critic_review"] is not None
        assert replan_payload["notification"] is not None

        evaluation = client.post("/api/v1/evaluation/run-sample", json={})
        assert evaluation.status_code == 200
        assert evaluation.json()["system_variant"] == "pathai_full"
        assert evaluation.json()["baseline_comparisons"]
