import pytest

from app.assessment.schemas import KnowledgeMap
from app.curriculum.llm import generate_curriculum_with_llm
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import CurriculumGenerationRequest


@pytest.mark.asyncio
async def test_mock_llm_curriculum_generation_returns_structured_plan() -> None:
    request = CurriculumGenerationRequest(
        goal="Learn RAG systems",
        timeline_weeks=4,
        hours_per_week=6,
        knowledge_map=KnowledgeMap(
            strong=["Python basics"],
            weak=["Embeddings"],
            missing=["Chunking"],
            recommended_level="beginner",
            confidence_score=0.8,
            assessment_notes=[],
        ),
    )
    deterministic = build_deterministic_curriculum(request)

    generated = await generate_curriculum_with_llm(request, deterministic)

    assert generated.source == "mock_llm"
    assert generated.curriculum_id == deterministic.curriculum_id
    assert len(generated.weeks) == 4
    assert generated.weeks[-1].project_or_application is True
