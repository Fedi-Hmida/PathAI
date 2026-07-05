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
from app.schemas.enums import OrchestrationStatus

CONTINUE = "continue"
STOP = "stop"

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
    graph = StateGraph(GraphState)
    for node_name in NODE_SEQUENCE:
        graph.add_node(node_name, cast(Any, _wrap_node(node_name, context)))

    graph.set_entry_point(NODE_SEQUENCE[0])
    for index, node_name in enumerate(NODE_SEQUENCE):
        if index == len(NODE_SEQUENCE) - 1:
            graph.add_edge(node_name, END)
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
