from app.agents.service import PathAIGraphService
from app.assessment.schemas import KnowledgeMap
from app.curriculum.graph import apply_curriculum_result_to_graph_state
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.rules import validate_curriculum_plan
from app.curriculum.schemas import CurriculumGenerationRequest, CurriculumGenerationResult


def test_curriculum_result_can_update_graph_state_curriculum_field() -> None:
    state = PathAIGraphService().create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn RAG systems",
        timeline_weeks=4,
        hours_per_week=6,
    )
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
    curriculum = build_deterministic_curriculum(request)
    result = CurriculumGenerationResult(
        curriculum=curriculum,
        validation_issues=validate_curriculum_plan(curriculum),
    )

    updated = apply_curriculum_result_to_graph_state(state, result)

    assert len(updated.curriculum) == 4
    assert updated.metadata["curriculum_id"] == curriculum.curriculum_id
    assert updated.metadata["curriculum_source"] == "deterministic"
