import pytest

from app.assessment.schemas import KnowledgeMap
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import CurriculumGenerationRequest, CurriculumPlan
from app.quiz.schemas import (
    QuizAnswer,
    QuizGenerationRequest,
    QuizSubmissionRequest,
)
from app.quiz.service import QuizService


def _curriculum() -> CurriculumPlan:
    return build_deterministic_curriculum(
        CurriculumGenerationRequest(
            goal="Learn RAG systems",
            timeline_weeks=4,
            hours_per_week=6,
            knowledge_map=KnowledgeMap(
                strong=["Python basics"],
                weak=["Embeddings"],
                missing=["Chunking", "Reranking"],
                recommended_level="beginner",
                confidence_score=0.84,
                assessment_notes=["Quiz test map."],
            ),
        )
    )


@pytest.mark.asyncio
async def test_quiz_generation_uses_curriculum_week_topics() -> None:
    service = QuizService()
    quiz = (
        await service.generate_quiz(
            QuizGenerationRequest(
                curriculum=_curriculum(),
                week_number=1,
                question_count=5,
            )
        )
    ).quiz

    assert len(quiz.questions) == 5
    assert quiz.week_number == 1
    assert quiz.topic_names
    assert {question.type for question in quiz.questions} >= {
        "multiple_choice",
        "true_false",
        "short_answer",
    }


@pytest.mark.asyncio
async def test_quiz_scoring_feedback_and_history() -> None:
    service = QuizService()
    quiz = (
        await service.generate_quiz(
            QuizGenerationRequest(
                curriculum=_curriculum(),
                week_number=1,
                question_count=5,
            )
        )
    ).quiz

    result = service.submit_quiz(
        quiz.quiz_id,
        QuizSubmissionRequest(
            answers=[
                QuizAnswer(
                    question_id=question.question_id,
                    answer=question.correct_answer,
                )
                for question in quiz.questions
            ]
        ),
    )

    history = service.get_history(quiz.curriculum_id)

    assert result.score == 1.0
    assert result.passed is True
    assert all(item.correct for item in result.attempt.feedback)
    assert history.best_score == 1.0
    assert len(history.attempts) == 1


@pytest.mark.asyncio
async def test_quiz_low_score_signal() -> None:
    service = QuizService()
    quiz = (
        await service.generate_quiz(
            QuizGenerationRequest(
                curriculum=_curriculum(),
                week_number=1,
                question_count=5,
            )
        )
    ).quiz

    result = service.submit_quiz(
        quiz.quiz_id,
        QuizSubmissionRequest(
            answers=[
                QuizAnswer(question_id=question.question_id, answer="wrong")
                for question in quiz.questions
            ]
        ),
    )

    history = service.get_history(quiz.curriculum_id)

    assert result.score == 0.0
    assert result.low_score_signal is True
    assert history.low_score_count == 1


@pytest.mark.asyncio
async def test_mock_llm_quiz_generation_stays_structured() -> None:
    service = QuizService()
    quiz = (
        await service.generate_quiz(
            QuizGenerationRequest(
                curriculum=_curriculum(),
                week_number=1,
                question_count=5,
                use_mock_llm=True,
            )
        )
    ).quiz

    assert len(quiz.questions) == 5
    assert quiz.quiz_id.startswith("quiz_")
