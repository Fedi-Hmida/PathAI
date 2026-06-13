import pytest

from app.agents.state import GraphState
from app.assessment.schemas import KnowledgeMap
from app.critic.graph import apply_critic_review_to_graph_state
from app.critic.schemas import CriticReviewRequest
from app.critic.service import CriticService
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import CurriculumGenerationRequest
from app.rag.schemas import CurriculumResourceAttachmentRequest
from app.rag.service import ResourceService


@pytest.mark.asyncio
async def test_critic_review_applies_to_graph_state_approval_path() -> None:
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
                assessment_notes=["Graph critic test."],
            ),
        )
    )
    resource_attachment = ResourceService().retrieve_for_curriculum(
        CurriculumResourceAttachmentRequest(curriculum=curriculum, top_k=2)
    )
    service = CriticService()
    review = await service.review_curriculum_with_resources(
        CriticReviewRequest(
            curriculum=curriculum,
            resource_attachment=resource_attachment,
            required_resources_per_topic=1,
        )
    )
    state = GraphState(
        user_id="demo-user",
        goal_id="demo-goal",
        goal="Learn RAG systems",
        timeline_weeks=4,
        hours_per_week=8,
    )

    updated = apply_critic_review_to_graph_state(state, review, service)

    assert updated.critic_review is not None
    assert updated.critic_review.approved is True
    assert updated.metadata["critic_review_id"] == review.review_id


@pytest.mark.asyncio
async def test_critic_review_applies_to_graph_state_rejection_path() -> None:
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
                assessment_notes=["Graph critic rejection test."],
            ),
        )
    )
    resource_attachment = ResourceService().retrieve_for_curriculum(
        CurriculumResourceAttachmentRequest(curriculum=curriculum, top_k=2)
    )
    service = CriticService()
    review = await service.review_curriculum_with_resources(
        CriticReviewRequest(
            curriculum=curriculum,
            resource_attachment=resource_attachment,
            required_resources_per_topic=2,
        )
    )
    state = GraphState(
        user_id="demo-user",
        goal_id="demo-goal",
        goal="Learn RAG systems",
        timeline_weeks=4,
        hours_per_week=8,
    )

    updated = apply_critic_review_to_graph_state(state, review, service)

    assert updated.critic_review is not None
    assert updated.critic_review.approved is False
    assert updated.revision_count == 1
