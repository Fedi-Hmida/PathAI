from __future__ import annotations

from app.api.v1.dependencies import ApiServiceContainer
from app.orchestration.runner import run_straight_line_demo_from_container


def test_progress_quiz_adaptation_events_are_safe_and_ordered() -> None:
    container = ApiServiceContainer()

    result = run_straight_line_demo_from_container(container)

    messages = [event.message for event in result.run.node_events if event.message]
    progress_index = messages.index("agent=progress artifact_id=progress_demo_rag")
    quiz_index = messages.index("agent=quiz artifact_id=quiz_demo_rag")
    adaptation_index = messages.index("agent=adapter artifact_id=adapt_demo_rag_retrieval")

    assert progress_index < quiz_index < adaptation_index
    for message in messages:
        normalized = message.lower()
        assert "correct_answer" not in normalized
        assert "answer_key" not in normalized
        assert "payload" not in normalized
        assert "traceback" not in normalized
        assert "secret" not in normalized


def test_progress_quiz_adaptation_events_do_not_store_large_artifacts() -> None:
    container = ApiServiceContainer()

    result = run_straight_line_demo_from_container(container)

    for event in result.run.node_events:
        dumped = event.model_dump_json().lower()
        assert "question_quiz_recall_k" not in dumped
        assert "relevant items appearing in the top k" not in dumped
        assert "practice recall and precision with toy retrieval results" not in dumped
        assert "retrieval metrics practice" not in dumped
