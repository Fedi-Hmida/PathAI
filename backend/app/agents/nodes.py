from collections.abc import Callable

from app.agents.constants import (
    ASSESSOR_NODE,
    CRITIC_NODE,
    CURRICULUM_NODE,
    FAILURE_NODE,
    NOTIFY_NODE,
    PERSIST_NODE,
    RESOURCE_NODE,
    START_NODE,
    NodeName,
)
from app.agents.state import CriticReview, GraphState, utc_now
from app.agents.tracing import add_error, add_warning, record_trace

GraphNode = Callable[[GraphState], GraphState]


def _begin(state: GraphState, node_name: NodeName) -> GraphState:
    return record_trace(state, node_name=node_name, status="started")


def _complete(state: GraphState, node_name: NodeName) -> GraphState:
    return record_trace(state, node_name=node_name, status="completed")


def _maybe_simulate_failure(state: GraphState, node_name: NodeName) -> GraphState:
    if state.metadata.get("simulate_failure_node") != node_name:
        return state
    failed = add_error(
        state,
        node_name=node_name,
        code="simulated_node_failure",
        message=f"Simulated failure from {node_name}.",
    )
    return record_trace(
        failed,
        node_name=node_name,
        status="failed",
        errors=["simulated_node_failure"],
    )


def start_node(state: GraphState) -> GraphState:
    current = _begin(state, START_NODE)
    current = _maybe_simulate_failure(current, START_NODE)
    if current.has_errors:
        return current
    current.current_stage = "started"
    current.job_status = "running"
    current.metadata["graph_started"] = True
    current.updated_at = utc_now()
    return _complete(current, START_NODE)


def assessor_node(state: GraphState) -> GraphState:
    current = _begin(state, ASSESSOR_NODE)
    current = _maybe_simulate_failure(current, ASSESSOR_NODE)
    if current.has_errors:
        return current
    current.current_stage = "assessing"
    current.knowledge_map = {
        "strong": [],
        "weak": ["deterministic placeholder gap"],
        "missing": ["real assessment agent"],
        "recommended_level": "beginner",
        "confidence_score": 0.75,
    }
    current.updated_at = utc_now()
    return _complete(current, ASSESSOR_NODE)


def curriculum_node(state: GraphState) -> GraphState:
    current = _begin(state, CURRICULUM_NODE)
    current = _maybe_simulate_failure(current, CURRICULUM_NODE)
    if current.has_errors:
        return current
    current.current_stage = "generating_curriculum"
    revision_label = f"revision {current.revision_count}" if current.revision_count else "initial"
    current.curriculum = [
        {
            "week_number": 1,
            "title": f"{revision_label.title()} PathAI placeholder week",
            "topics": [
                {
                    "topic_id": "placeholder-topic-1",
                    "title": "Graph orchestration foundations",
                    "status": "pending",
                }
            ],
        }
    ]
    current.updated_at = utc_now()
    return _complete(current, CURRICULUM_NODE)


def resource_node(state: GraphState) -> GraphState:
    current = _begin(state, RESOURCE_NODE)
    current = _maybe_simulate_failure(current, RESOURCE_NODE)
    if current.has_errors:
        return current
    current.current_stage = "attaching_resources"
    current.resources = [
        {
            "topic_id": "placeholder-topic-1",
            "title": "Placeholder resource for graph tests",
            "scope": current.resource_refresh_scope,
            "source": "deterministic_stub",
        }
    ]
    current.metadata["resource_node_called"] = True
    current.updated_at = utc_now()
    return _complete(current, RESOURCE_NODE)


def critic_node(state: GraphState) -> GraphState:
    current = _begin(state, CRITIC_NODE)
    current = _maybe_simulate_failure(current, CRITIC_NODE)
    if current.has_errors:
        return current
    current.current_stage = "reviewing"
    reject_until = int(current.metadata.get("critic_reject_until_revision", 0))

    if current.revision_count < reject_until:
        next_revision_count = current.revision_count + 1
        auto_approve = next_revision_count >= current.max_revisions
        current.revision_count = next_revision_count
        if auto_approve:
            current.critic_review = CriticReview(
                decision="auto_approved",
                approved=True,
                score=0.62,
                auto_approved=True,
                revision_instructions=None,
            )
            current = add_warning(
                current,
                node_name=CRITIC_NODE,
                code="max_revisions_reached",
                message="Auto-approved after max revision count; requires manual review.",
            )
        else:
            current.critic_review = CriticReview(
                decision="revise",
                approved=False,
                score=0.58,
                revision_instructions="Improve topic sequencing and resource coverage.",
            )
    else:
        current.critic_review = CriticReview(
            decision="approved",
            approved=True,
            score=0.86,
            revision_instructions=None,
        )

    current.updated_at = utc_now()
    return _complete(current, CRITIC_NODE)


def persist_node(state: GraphState) -> GraphState:
    current = _begin(state, PERSIST_NODE)
    current = _maybe_simulate_failure(current, PERSIST_NODE)
    if current.has_errors:
        return current
    current.current_stage = "persisting"
    current.metadata["persist_placeholder"] = "no_database_write_in_phase_3"
    current.updated_at = utc_now()
    return _complete(current, PERSIST_NODE)


def notify_node(state: GraphState) -> GraphState:
    current = _begin(state, NOTIFY_NODE)
    current = _maybe_simulate_failure(current, NOTIFY_NODE)
    if current.has_errors:
        return current
    current.current_stage = "completed"
    current.job_status = "completed"
    current.metadata["notification_placeholder"] = "no_notification_sent_in_phase_3"
    current.updated_at = utc_now()
    return _complete(current, NOTIFY_NODE)


def failure_node(state: GraphState) -> GraphState:
    current = _begin(state, FAILURE_NODE)
    current.current_stage = "failed"
    current.job_status = "failed"
    if not current.errors:
        current = add_error(
            current,
            node_name=FAILURE_NODE,
            code="unknown_graph_failure",
            message="Graph failed without a node-specific error.",
        )
    current.metadata["user_safe_message"] = "The graph run failed safely before completion."
    current.updated_at = utc_now()
    return _complete(current, FAILURE_NODE)


NODE_FUNCTIONS: dict[NodeName, GraphNode] = {
    START_NODE: start_node,
    ASSESSOR_NODE: assessor_node,
    CURRICULUM_NODE: curriculum_node,
    RESOURCE_NODE: resource_node,
    CRITIC_NODE: critic_node,
    PERSIST_NODE: persist_node,
    NOTIFY_NODE: notify_node,
    FAILURE_NODE: failure_node,
}
