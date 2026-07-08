from __future__ import annotations

from pathlib import Path

from app.api.v1.dependencies import ApiServiceContainer
from app.orchestration.runner import run_straight_line_demo_from_container

APP_DIR = Path(__file__).resolve().parents[1]

REBUILD_10_FILES = (
    APP_DIR / "agents" / "deterministic" / "progress.py",
    APP_DIR / "agents" / "deterministic" / "quiz.py",
    APP_DIR / "agents" / "deterministic" / "adaptation.py",
    APP_DIR / "agents" / "mock" / "progress.py",
    APP_DIR / "agents" / "mock" / "quiz.py",
    APP_DIR / "agents" / "mock" / "adaptation.py",
    APP_DIR / "agents" / "services" / "progress.py",
    APP_DIR / "agents" / "services" / "quiz.py",
    APP_DIR / "agents" / "services" / "adaptation.py",
    APP_DIR / "orchestration" / "nodes.py",
)

FORBIDDEN_REFERENCES = (
    ".env",
    "app.api.v1",
    "app.llm",
    "beanie",
    "docker",
    "fastapi",
    "frontend",
    "httpx",
    "jwt",
    "langchain",
    "mongodb",
    "motor",
    "openai",
    "pymongo",
    "requests",
)


def test_rebuild_10_modules_do_not_reference_forbidden_boundaries() -> None:
    for path in REBUILD_10_FILES:
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in FORBIDDEN_REFERENCES:
            assert forbidden not in text, f"{path.name} references forbidden {forbidden}"


def test_workflow_state_keeps_feedback_artifacts_lightweight() -> None:
    container = ApiServiceContainer()

    result = run_straight_line_demo_from_container(container)
    state_payload = result.state.model_dump()
    state_text = str(state_payload).lower()

    assert state_payload["progress_state_id"] == "progress_demo_rag"
    assert state_payload["quiz_id"] == "quiz_demo_rag"
    assert state_payload["quiz_attempt_id"] == "attempt_demo_rag_low_score"
    assert state_payload["adaptation_event_ids"] == ["adapt_demo_rag_retrieval"]
    assert isinstance(state_payload["quiz_score"], float)
    assert "correct_answer" not in state_text
    assert "selected_options" not in state_text
    assert "question_quiz" not in state_text
    assert "before_summary" not in state_text
    assert "after_summary" not in state_text
