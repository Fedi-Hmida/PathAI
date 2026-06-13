from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.agents.demo_orchestration import (
    ServiceBackedDemoOrchestrator,
    ServiceBackedDemoRequest,
)
from app.db.mongodb import database_manager
from app.main import app


@pytest.mark.asyncio
async def test_service_backed_demo_orchestrator_runs_real_modules() -> None:
    result = await ServiceBackedDemoOrchestrator().run(
        ServiceBackedDemoRequest(
            goal="Learn RAG systems for a graduation project",
            assessment_answer="Embeddings map text into vectors for retrieval.",
            timeline_weeks=4,
            hours_per_week=6,
            quiz_question_count=3,
        )
    )

    assert result.run_id.startswith("demo_")
    assert [step.name for step in result.steps] == [
        "Assessment started",
        "Assessment answer submitted",
        "Knowledge map finalized",
        "Curriculum generated",
        "Resources attached",
        "Critic review completed",
        "Progress updated",
        "Quiz completed",
        "Adapter flow completed",
        "Synthetic evaluation generated",
    ]
    assert result.curriculum.weeks
    assert result.resource_attachment.attachments
    assert result.critic_review.decision in {"approved", "rejected", "auto_approved"}
    assert result.progress_summary.analytics.stuck_topic_count >= 1
    assert result.quiz_result.score == 1.0
    assert result.adaptation_decision.should_replan is True
    assert result.adaptation_result.decision.decision == "replanned"
    assert result.evaluation_report.system_variant == "pathai_full"


def test_service_backed_demo_endpoint_uses_real_services(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(database_manager, "connect", AsyncMock())
    monkeypatch.setattr(database_manager, "close", AsyncMock())

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/dev/graph/service-backed-demo-run",
            json={
                "goal": "Learn RAG systems for AI engineering",
                "assessment_answer": "Embeddings represent text for semantic search.",
                "timeline_weeks": 4,
                "hours_per_week": 6,
                "quiz_question_count": 3,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["steps"][-1]["name"] == "Synthetic evaluation generated"
    assert payload["curriculum"]["weeks"]
    assert payload["resource_attachment"]["attachments"]
    assert payload["quiz_result"]["score"] == 1.0
    assert payload["adaptation_result"]["decision"]["decision"] == "replanned"
    assert "placeholder" not in " ".join(step["summary"] for step in payload["steps"]).lower()
