from app.agents.state import GraphState
from app.assessment.schemas import KnowledgeMap
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import CurriculumGenerationRequest
from app.rag.graph import (
    apply_resource_attachment_to_graph_state,
    apply_resource_results_to_graph_state,
)
from app.rag.schemas import CurriculumResourceAttachmentRequest, ResourceRetrievalRequest
from app.rag.service import ResourceService


def test_resource_retrieval_output_fits_graph_state() -> None:
    service = ResourceService()
    result = service.retrieve_for_topic(
        ResourceRetrievalRequest(topic="Embeddings", difficulty="beginner", top_k=2)
    )
    state = GraphState(
        user_id="demo-user",
        goal_id="demo-goal",
        goal="Learn RAG systems",
        timeline_weeks=4,
        hours_per_week=6,
    )

    updated = apply_resource_results_to_graph_state(state, [result])

    assert updated.resources
    assert updated.metadata["resource_result_count"] == 1


def test_resource_attachment_output_updates_graph_curriculum_state() -> None:
    curriculum = build_deterministic_curriculum(
        CurriculumGenerationRequest(
            goal="Learn RAG systems",
            timeline_weeks=3,
            hours_per_week=6,
            knowledge_map=KnowledgeMap(
                strong=["Python basics"],
                weak=["Embeddings"],
                missing=["Chunking", "Reranking"],
                recommended_level="beginner",
                confidence_score=0.84,
                assessment_notes=["Graph compatibility test."],
            ),
        )
    )
    service = ResourceService()
    response = service.retrieve_for_curriculum(
        CurriculumResourceAttachmentRequest(curriculum=curriculum, top_k=2)
    )
    state = GraphState(
        user_id="demo-user",
        goal_id="demo-goal",
        goal="Learn RAG systems",
        timeline_weeks=3,
        hours_per_week=6,
    )

    updated = apply_resource_attachment_to_graph_state(state, response)

    assert updated.curriculum
    assert updated.resources
    assert updated.metadata["resource_attachment_curriculum_id"] == curriculum.curriculum_id
