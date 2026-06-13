from app.agents.service import PathAIGraphService
from app.assessment.graph import apply_assessment_result_to_graph_state
from app.assessment.schemas import AssessmentProgress, FinalAssessmentResult, KnowledgeMap


def test_assessment_result_can_update_graph_state_knowledge_map() -> None:
    state = PathAIGraphService().create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn RAG systems",
        timeline_weeks=8,
        hours_per_week=10,
    )
    result = FinalAssessmentResult(
        session_id="session-1",
        knowledge_map=KnowledgeMap(
            strong=["Embeddings"],
            weak=["Reranking"],
            missing=["Prompt Injection"],
            recommended_level="intermediate",
            confidence_score=0.82,
            assessment_notes=["Test map."],
        ),
        progress=AssessmentProgress(
            answered_count=4,
            asked_count=4,
            max_questions=8,
            confidence_score=0.82,
            current_difficulty="intermediate",
            status="completed",
            enough_evidence=True,
        ),
    )

    updated = apply_assessment_result_to_graph_state(state, result)

    assert updated.knowledge_map["recommended_level"] == "intermediate"
    assert updated.knowledge_map["strong"] == ["Embeddings"]
    assert updated.metadata["assessment_session_id"] == "session-1"
