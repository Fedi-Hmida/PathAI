from typing import Any

from app.agents.state import GraphState
from app.rag.schemas import CurriculumResourceAttachmentResponse, ResourceRetrievalResult


def resource_results_to_graph_payload(
    results: list[ResourceRetrievalResult],
) -> list[dict[str, Any]]:
    return [result.model_dump(mode="json") for result in results]


def apply_resource_results_to_graph_state(
    state: GraphState,
    results: list[ResourceRetrievalResult],
) -> GraphState:
    updated = state.model_copy(deep=True)
    updated.resources = resource_results_to_graph_payload(results)
    updated.metadata["resource_result_count"] = len(results)
    return updated


def apply_resource_attachment_to_graph_state(
    state: GraphState,
    response: CurriculumResourceAttachmentResponse,
) -> GraphState:
    updated = apply_resource_results_to_graph_state(state, response.topic_results)
    updated.curriculum = response.enriched_curriculum.get("weeks", [])
    updated.metadata["resource_attachment_curriculum_id"] = response.curriculum_id
    updated.metadata["resource_warning_count"] = len(response.warnings)
    return updated
