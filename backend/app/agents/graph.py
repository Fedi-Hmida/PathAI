from typing import Any

from app.agents.constants import (
    ASSESSOR_NODE,
    CRITIC_NODE,
    CURRICULUM_NODE,
    DEFAULT_MAX_REVISIONS,
    END_NODE,
    FAILURE_NODE,
    GRAPH_EDGES,
    GRAPH_NODES,
    NOTIFY_NODE,
    PERSIST_NODE,
    RESOURCE_NODE,
    START_NODE,
    NodeName,
)
from app.agents.errors import LangGraphDependencyError
from app.agents.nodes import NODE_FUNCTIONS
from app.agents.state import GraphState


def route_after_node(state: GraphState, current_node: NodeName) -> str:
    if current_node == FAILURE_NODE:
        return END_NODE
    if current_node == NOTIFY_NODE:
        return END_NODE
    if state.has_errors:
        return FAILURE_NODE

    if current_node == START_NODE:
        return ASSESSOR_NODE
    if current_node == ASSESSOR_NODE:
        return CURRICULUM_NODE
    if current_node == CURRICULUM_NODE:
        return RESOURCE_NODE
    if current_node == RESOURCE_NODE:
        return CRITIC_NODE
    if current_node == CRITIC_NODE:
        return route_after_critic(state)
    if current_node == PERSIST_NODE:
        return NOTIFY_NODE
    return FAILURE_NODE


def route_after_critic(state: GraphState) -> str:
    if state.has_errors:
        return FAILURE_NODE
    if state.critic_review is None:
        return FAILURE_NODE
    if state.critic_review.approved:
        return PERSIST_NODE
    if state.revision_count >= state.max_revisions:
        return PERSIST_NODE
    return CURRICULUM_NODE


def get_graph_definition_summary() -> dict[str, Any]:
    return {
        "graph_version": "pathai.graph.v1",
        "nodes": GRAPH_NODES,
        "edges": GRAPH_EDGES,
        "conditional_routes": {
            "after_each_standard_node": "route to failure_node if errors exist",
            "critic_approved": f"{CRITIC_NODE} -> {PERSIST_NODE}",
            "critic_rejected_below_max": f"{CRITIC_NODE} -> {CURRICULUM_NODE}",
            "critic_rejected_at_max": f"{CRITIC_NODE} -> {PERSIST_NODE}",
            "failure": f"{FAILURE_NODE} -> {END_NODE}",
        },
        "default_max_revisions": DEFAULT_MAX_REVISIONS,
        "checkpoint_strategy": "in_memory_for_phase_3; future database-backed store",
        "real_llm_calls": False,
        "database_writes": False,
    }


def build_langgraph_app() -> Any:
    try:
        from langgraph.graph import END, START, StateGraph
    except ModuleNotFoundError as exc:
        raise LangGraphDependencyError(
            "LangGraph is not installed. Install requirements before building the compiled graph."
        ) from exc

    def wrap_node(node_name: NodeName) -> Any:
        def _wrapped(raw_state: GraphState | dict[str, Any]) -> dict[str, Any]:
            state = _coerce_graph_state(raw_state)
            next_state = NODE_FUNCTIONS[node_name](state)
            return next_state.model_dump(mode="json")

        return _wrapped

    workflow = StateGraph(GraphState)
    for node_name in GRAPH_NODES:
        workflow.add_node(node_name, wrap_node(node_name))

    workflow.add_edge(START, START_NODE)
    workflow.add_conditional_edges(START_NODE, _route_dict_after(START_NODE))
    workflow.add_conditional_edges(ASSESSOR_NODE, _route_dict_after(ASSESSOR_NODE))
    workflow.add_conditional_edges(CURRICULUM_NODE, _route_dict_after(CURRICULUM_NODE))
    workflow.add_conditional_edges(RESOURCE_NODE, _route_dict_after(RESOURCE_NODE))
    workflow.add_conditional_edges(CRITIC_NODE, _route_dict_after(CRITIC_NODE))
    workflow.add_conditional_edges(PERSIST_NODE, _route_dict_after(PERSIST_NODE))
    workflow.add_conditional_edges(NOTIFY_NODE, _route_dict_after(NOTIFY_NODE), {END_NODE: END})
    workflow.add_conditional_edges(FAILURE_NODE, _route_dict_after(FAILURE_NODE), {END_NODE: END})
    return workflow.compile()


def _route_dict_after(node_name: NodeName) -> Any:
    def _route(raw_state: GraphState | dict[str, Any]) -> str:
        return route_after_node(_coerce_graph_state(raw_state), node_name)

    return _route


def _coerce_graph_state(raw_state: GraphState | dict[str, Any]) -> GraphState:
    if isinstance(raw_state, GraphState):
        return raw_state
    return GraphState.model_validate(raw_state)
