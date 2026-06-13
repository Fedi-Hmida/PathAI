from app.agents.state import GraphState
from app.agents.tracing import add_warning
from app.critic.schemas import CriticReviewResult
from app.critic.service import CriticService


def apply_critic_review_to_graph_state(
    state: GraphState,
    result: CriticReviewResult,
    service: CriticService | None = None,
) -> GraphState:
    critic_service = service or CriticService()
    updated = state.model_copy(deep=True)
    updated.critic_review = critic_service.to_graph_critic_review(result)
    updated.metadata["critic_review_id"] = result.review_id
    updated.metadata["critic_quality_score"] = result.overall_quality_score
    updated.metadata["critic_issue_count"] = len(result.curriculum_issues) + len(
        result.resource_issues
    )
    if not result.approved:
        updated.revision_count = min(updated.revision_count + 1, updated.max_revisions)
    if result.auto_approved:
        updated = add_warning(
            updated,
            node_name="critic_node",
            code="critic_auto_approved",
            message="Critic forced approval after max revision count; manual review required.",
        )
    return updated
