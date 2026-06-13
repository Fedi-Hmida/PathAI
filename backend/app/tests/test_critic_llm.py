import pytest

from app.assessment.schemas import KnowledgeMap
from app.critic.schemas import CriticReviewRequest
from app.critic.service import CriticService
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import CurriculumGenerationRequest
from app.rag.schemas import CurriculumResourceAttachmentRequest
from app.rag.service import ResourceService


@pytest.mark.asyncio
async def test_mock_llm_critic_path_returns_structured_review_without_real_llm() -> None:
    curriculum = build_deterministic_curriculum(
        CurriculumGenerationRequest(
            goal="Learn RAG systems",
            timeline_weeks=4,
            hours_per_week=8,
            knowledge_map=KnowledgeMap(
                strong=["Python basics"],
                weak=["Embeddings"],
                missing=["Chunking", "Reranking"],
                recommended_level="beginner",
                confidence_score=0.84,
                assessment_notes=["Critic mock LLM test."],
            ),
        )
    )
    resource_attachment = ResourceService().retrieve_for_curriculum(
        CurriculumResourceAttachmentRequest(curriculum=curriculum, top_k=2)
    )

    review = await CriticService().review_curriculum_with_resources(
        CriticReviewRequest(
            curriculum=curriculum,
            resource_attachment=resource_attachment,
            required_resources_per_topic=1,
            use_mock_llm=True,
        )
    )

    assert review.source == "mock_llm"
    assert review.approved is True
