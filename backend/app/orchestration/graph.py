from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from langgraph.graph import END, StateGraph

from app.orchestration.nodes import (
    NODE_SEQUENCE,
    OrchestrationContext,
    complete_run,
    initialize_run,
    load_adaptation,
    load_assessment,
    load_critic_review,
    load_curriculum,
    load_evaluation,
    load_goal,
    load_knowledge_map,
    load_progress,
    load_quiz,
    load_resources,
    prepare_dashboard_payload,
    run_node,
)
from app.orchestration.state import GraphState
from app.schemas.enums import CriticPassStatus, OrchestrationStatus

CONTINUE = "continue"
STOP = "stop"
REVISE = "revise"

REVIEW_NODE = "load_critic_review"
CURRICULUM_NODE = "load_curriculum"

# Hard cap on curriculum re-generations driven by the critic's `should_revise_curriculum`
# loop (MAIN.md §7.3). Inert until the conditional re-entry edge is wired (Rebuild-23C);
# defined here now so the counter primitive and its bound live in one place.
MAX_CRITIC_REVISION_ATTEMPTS = 1

NODE_BODIES = {
    "initialize_run": initialize_run,
    "load_goal": load_goal,
    "load_assessment": load_assessment,
    "load_knowledge_map": load_knowledge_map,
    "load_curriculum": load_curriculum,
    "load_resources": load_resources,
    "load_critic_review": load_critic_review,
    "load_progress": load_progress,
    "load_quiz": load_quiz,
    "load_adaptation": load_adaptation,
    "load_evaluation": load_evaluation,
    "prepare_dashboard_payload": prepare_dashboard_payload,
    "complete_run": complete_run,
}


def build_straight_line_graph(context: OrchestrationContext) -> Any:
    """Build the single-pass generation graph plus the one bounded revision loop.

    Every node is straight-line except ``load_critic_review``, which routes through
    ``should_revise_curriculum`` (MAIN.md §7.3): on a critic verdict of REVISE/FAILED,
    and while under ``MAX_CRITIC_REVISION_ATTEMPTS``, it re-enters ``load_curriculum``
    (→ resources → critic) to regenerate with the critic's recommendations; otherwise
    it continues to ``load_progress``. The loop is hard-capped, so it always terminates.
    """
    graph = StateGraph(GraphState)
    for node_name in NODE_SEQUENCE:
        graph.add_node(node_name, cast(Any, _wrap_node(node_name, context)))

    graph.set_entry_point(NODE_SEQUENCE[0])
    for index, node_name in enumerate(NODE_SEQUENCE):
        if index == len(NODE_SEQUENCE) - 1:
            graph.add_edge(node_name, END)
        elif node_name == REVIEW_NODE:
            graph.add_conditional_edges(
                node_name,
                should_revise_curriculum,
                {
                    REVISE: CURRICULUM_NODE,
                    CONTINUE: NODE_SEQUENCE[index + 1],
                    STOP: END,
                },
            )
        else:
            graph.add_conditional_edges(
                node_name,
                _route_after_node,
                {
                    CONTINUE: NODE_SEQUENCE[index + 1],
                    STOP: END,
                },
            )
    return graph.compile()


def _wrap_node(
    node_name: str,
    context: OrchestrationContext,
) -> Callable[[GraphState], GraphState]:
    body = NODE_BODIES[node_name]

    def wrapped(state: GraphState) -> GraphState:
        return run_node(node_name, state, context, body)

    return wrapped


def _route_after_node(state: GraphState) -> str:
    if state["status"] == OrchestrationStatus.FAILED:
        return STOP
    return CONTINUE


def should_revise_curriculum(state: GraphState) -> str:
    """Decide, after a critic review, whether to revise the curriculum (MAIN.md §7.3).

    Pure state → edge-key function, exactly like ``_route_after_node``; it reads only
    the lightweight signal ``load_critic_review`` recorded (``critic_pass_status``) and
    the revision counter ``load_curriculum`` maintains (``critic_revision_attempts``).
    It never touches persistence and never mutates state — the counter is incremented
    inside ``load_curriculum`` on re-entry, since a router can only pick an edge.
    """
    if state["status"] == OrchestrationStatus.FAILED:
        return STOP
    pass_status = state.get("critic_pass_status")
    attempts = state.get("critic_revision_attempts", 0)
    needs_revision = pass_status in (CriticPassStatus.REVISE, CriticPassStatus.FAILED)
    if needs_revision and attempts < MAX_CRITIC_REVISION_ATTEMPTS:
        return REVISE
    return CONTINUE
