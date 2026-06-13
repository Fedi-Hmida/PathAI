import pytest

from app.assessment.schemas import AnswerSubmissionRequest, GoalIntakeRequest
from app.assessment.service import AssessmentService


@pytest.mark.asyncio
async def test_start_assessment_creates_session_and_first_question() -> None:
    service = AssessmentService()
    response = await service.start_assessment(
        GoalIntakeRequest(
            goal="Learn RAG systems for my graduation project",
            timeline_weeks=8,
            hours_per_week=10,
            target_level="intermediate",
        )
    )

    assert response.session.status == "in_progress"
    assert response.session.user_id == "demo-user"
    assert response.session.question_index == 1
    assert response.next_question.topic == "Embeddings"
    assert response.next_question.source == "mock_llm"


@pytest.mark.asyncio
async def test_answer_submission_updates_difficulty_and_evidence() -> None:
    service = AssessmentService()
    started = await service.start_assessment(
        GoalIntakeRequest(
            goal="Learn RAG systems",
            timeline_weeks=8,
            hours_per_week=10,
            target_level="beginner",
        )
    )

    response = await service.submit_answer(
        started.session.session_id,
        AnswerSubmissionRequest(answer="It is a vector representation for semantic similarity."),
    )

    assert response.evaluation is not None
    assert response.evaluation.signal == "strong"
    assert response.session.current_difficulty == "intermediate"
    assert response.next_question is not None


@pytest.mark.asyncio
async def test_idk_answer_is_gap_signal() -> None:
    service = AssessmentService()
    started = await service.start_assessment(
        GoalIntakeRequest(
            goal="Learn RAG systems",
            timeline_weeks=8,
            hours_per_week=10,
            target_level="intermediate",
        )
    )

    response = await service.submit_answer(
        started.session.session_id,
        AnswerSubmissionRequest(answer="I don't know"),
    )

    assert response.evaluation is not None
    assert response.evaluation.is_idk is True
    assert response.evaluation.signal == "missing"
    assert response.session.current_difficulty == "beginner"


@pytest.mark.asyncio
async def test_max_questions_finalizes_knowledge_map() -> None:
    service = AssessmentService()
    started = await service.start_assessment(
        GoalIntakeRequest(
            goal="Learn RAG systems",
            timeline_weeks=8,
            hours_per_week=10,
            target_level="intermediate",
            max_questions=3,
        )
    )
    session_id = started.session.session_id

    first = await service.submit_answer(
        session_id,
        AnswerSubmissionRequest(answer="A vector representation for semantic similarity."),
    )
    assert first.result is None

    second = await service.submit_answer(
        session_id,
        AnswerSubmissionRequest(answer="Chunk size affects context window and semantic coherence."),
    )
    assert second.result is None

    final = await service.submit_answer(
        session_id,
        AnswerSubmissionRequest(
            answer="Vector database supports nearest neighbors similarity search.",
        ),
    )

    assert final.result is not None
    assert final.session.status == "completed"
    assert final.result.knowledge_map.confidence_score > 0.0
    assert final.result.knowledge_map.strong


@pytest.mark.asyncio
async def test_finalize_requires_at_least_one_answer() -> None:
    service = AssessmentService()
    started = await service.start_assessment(
        GoalIntakeRequest(
            goal="Learn RAG systems",
            timeline_weeks=8,
            hours_per_week=10,
            target_level="intermediate",
        )
    )

    with pytest.raises(Exception) as exc_info:
        service.finalize_assessment(started.session.session_id)

    assert "At least one answer is required" in str(exc_info.value)
