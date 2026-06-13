from typing import Any

from app.agents.state import GraphState
from app.assessment.schemas import FinalAssessmentResult, KnowledgeMap


def knowledge_map_to_graph_payload(knowledge_map: KnowledgeMap) -> dict[str, Any]:
    return knowledge_map.model_dump(mode="json")


def apply_assessment_result_to_graph_state(
    state: GraphState,
    result: FinalAssessmentResult,
) -> GraphState:
    updated = state.model_copy(deep=True)
    updated.knowledge_map = knowledge_map_to_graph_payload(result.knowledge_map)
    updated.metadata["assessment_session_id"] = result.session_id
    updated.metadata["assessment_confidence_score"] = result.knowledge_map.confidence_score
    return updated
