from app.agents.constants import (
    CRITIC_NODE,
    CURRICULUM_NODE,
    FAILURE_NODE,
    PERSIST_NODE,
)
from app.agents.graph import get_graph_definition_summary, route_after_critic, route_after_node
from app.agents.service import PathAIGraphService
from app.agents.state import CriticReview
from app.agents.tracing import add_error


def test_graph_definition_contains_required_nodes_and_edges() -> None:
    definition = get_graph_definition_summary()

    assert "assessor_node" in definition["nodes"]
    assert "curriculum_node" in definition["nodes"]
    assert "resource_node" in definition["nodes"]
    assert "critic_node" in definition["nodes"]
    assert definition["real_llm_calls"] is False
    assert definition["database_writes"] is False


def test_route_after_critic_approved() -> None:
    state = PathAIGraphService().create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn RAG",
        timeline_weeks=6,
        hours_per_week=8,
    )
    state.critic_review = CriticReview(decision="approved", approved=True, score=0.9)

    assert route_after_critic(state) == PERSIST_NODE


def test_route_after_critic_rejected_below_max() -> None:
    state = PathAIGraphService().create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn RAG",
        timeline_weeks=6,
        hours_per_week=8,
    )
    state.revision_count = 1
    state.max_revisions = 3
    state.critic_review = CriticReview(
        decision="revise",
        approved=False,
        score=0.55,
        revision_instructions="Improve sequencing.",
    )

    assert route_after_critic(state) == CURRICULUM_NODE


def test_route_after_critic_rejected_at_max() -> None:
    state = PathAIGraphService().create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn RAG",
        timeline_weeks=6,
        hours_per_week=8,
        max_revisions=1,
    )
    state.revision_count = 1
    state.critic_review = CriticReview(
        decision="revise",
        approved=False,
        score=0.55,
        revision_instructions="Improve sequencing.",
    )

    assert route_after_critic(state) == PERSIST_NODE


def test_route_to_failure_when_state_has_error() -> None:
    state = PathAIGraphService().create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn RAG",
        timeline_weeks=6,
        hours_per_week=8,
    )
    failed_state = add_error(state, "assessor_node", "test_error", "test")

    assert route_after_node(failed_state, CRITIC_NODE) == FAILURE_NODE
