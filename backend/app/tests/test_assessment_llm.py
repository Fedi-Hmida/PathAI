import pytest
from pydantic import ValidationError

from app.assessment.llm import generate_assessment_question
from app.assessment.question_bank import build_question_bank
from app.assessment.schemas import GoalIntakeRequest, KnowledgeMap


@pytest.mark.asyncio
async def test_mock_llm_question_generation_uses_structured_output() -> None:
    fallback = build_question_bank("Learn RAG systems", "intermediate")[0]

    generated = await generate_assessment_question(
        goal="Learn RAG systems",
        fallback_question=fallback,
    )

    assert generated.source == "mock_llm"
    assert generated.prompt == fallback.prompt
    assert generated.expected_concepts == fallback.expected_concepts


def test_goal_validation_normalizes_goal() -> None:
    goal = GoalIntakeRequest(
        goal="  Learn RAG systems   deeply ",
        timeline_weeks=8,
        hours_per_week=10,
    )

    assert goal.goal == "Learn RAG systems deeply"


def test_knowledge_map_schema_validation() -> None:
    with pytest.raises(ValidationError):
        KnowledgeMap(
            strong=[],
            weak=[],
            missing=[],
            recommended_level="beginner",
            confidence_score=1.5,
        )
