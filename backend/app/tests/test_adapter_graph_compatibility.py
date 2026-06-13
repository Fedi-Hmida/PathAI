import pytest

from app.adapter.graph import apply_adaptation_result_to_graph_state
from app.adapter.schemas import AdaptationReplanRequest
from app.adapter.service import AdapterService
from app.agents.state import GraphState
from app.assessment.schemas import KnowledgeMap
from app.curriculum.planner import build_deterministic_curriculum
from app.curriculum.schemas import CurriculumGenerationRequest, CurriculumPlan
from app.progress.schemas import ProgressInitializeRequest
from app.progress.service import ProgressService
from app.quiz.schemas import QuizAttempt, QuizHistorySummary


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
                assessment_notes=["Adapter graph test map."],
            ),
        )
    )


@pytest.mark.asyncio
async def test_adapter_result_fits_graph_state() -> None:
    curriculum = _curriculum()
    progress = ProgressService().initialize_progress(
        ProgressInitializeRequest(curriculum=curriculum)
    ).summary
    quiz_history = QuizHistorySummary(
        curriculum_id=curriculum.curriculum_id,
        attempts=[
            QuizAttempt(
                quiz_id="quiz-graph",
                curriculum_id=curriculum.curriculum_id,
                week_number=1,
                score=0.2,
                passed=False,
            )
        ],
        best_score=0.2,
        average_score=0.2,
        low_score_count=1,
    )
    result = await AdapterService().run_replan(
        AdaptationReplanRequest(
            curriculum=curriculum,
            progress_summary=progress,
            quiz_history=quiz_history,
            expected_week_number=1,
        )
    )
    state = GraphState(
        user_id="demo-user",
        goal_id="goal-1",
        goal=curriculum.goal,
        timeline_weeks=curriculum.timeline_weeks,
        hours_per_week=curriculum.hours_per_week,
    )

    updated = apply_adaptation_result_to_graph_state(state, result)

    assert updated.metadata["adaptation_id"] == result.adaptation_id
    assert updated.metadata["adaptation_should_replan"] is True
    assert updated.progress
