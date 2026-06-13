from typing import Any

from app.agents.state import GraphState
from app.curriculum.schemas import CurriculumGenerationResult, CurriculumPlan


def curriculum_to_graph_payload(curriculum: CurriculumPlan) -> list[dict[str, Any]]:
    return [week.model_dump(mode="json") for week in curriculum.weeks]


def apply_curriculum_result_to_graph_state(
    state: GraphState,
    result: CurriculumGenerationResult,
) -> GraphState:
    updated = state.model_copy(deep=True)
    updated.curriculum = curriculum_to_graph_payload(result.curriculum)
    updated.metadata["curriculum_id"] = result.curriculum.curriculum_id
    updated.metadata["curriculum_source"] = result.curriculum.source
    updated.metadata["curriculum_total_hours"] = result.curriculum.total_hours
    return updated
