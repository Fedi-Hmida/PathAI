from typing import Any

from app.agents.checkpointing import CheckpointStore, InMemoryCheckpointStore
from app.agents.constants import END_NODE, MAX_GRAPH_STEPS, START_NODE, NodeName
from app.agents.errors import GraphExecutionError
from app.agents.graph import get_graph_definition_summary, route_after_node
from app.agents.nodes import NODE_FUNCTIONS, failure_node
from app.agents.state import GraphState
from app.agents.tracing import add_error


class PathAIGraphService:
    def __init__(self, checkpoint_store: CheckpointStore | None = None) -> None:
        self.checkpoint_store = checkpoint_store or InMemoryCheckpointStore()

    def create_initial_state(
        self,
        user_id: str,
        goal_id: str,
        goal: str,
        timeline_weeks: int,
        hours_per_week: int,
        max_revisions: int = 3,
        metadata: dict[str, Any] | None = None,
    ) -> GraphState:
        return GraphState(
            user_id=user_id,
            goal_id=goal_id,
            goal=goal,
            timeline_weeks=timeline_weeks,
            hours_per_week=hours_per_week,
            max_revisions=max_revisions,
            metadata=metadata or {},
        )

    def run_demo_graph(self, initial_state: GraphState) -> GraphState:
        current_node: str = START_NODE
        state = initial_state.model_copy(deep=True)

        for _step in range(MAX_GRAPH_STEPS):
            if current_node == END_NODE:
                return state

            if current_node not in NODE_FUNCTIONS:
                state = add_error(
                    state,
                    node_name=str(current_node),
                    code="unknown_graph_node",
                    message=f"Unknown graph node: {current_node}.",
                    recoverable=False,
                )
                state = failure_node(state)
                self.checkpoint_store.save(state)
                return state

            node_name = current_node
            try:
                state = NODE_FUNCTIONS[node_name](state)
            except Exception as exc:
                state = add_error(
                    state,
                    node_name=node_name,
                    code="node_exception",
                    message=str(exc),
                    recoverable=True,
                )
                state = failure_node(state)
                self.checkpoint_store.save(state)
                return state

            self.checkpoint_store.save(state)
            current_node = route_after_node(state, node_name)

        raise GraphExecutionError("Graph exceeded the maximum deterministic step count.")

    def get_graph_definition_summary(self) -> dict[str, Any]:
        return get_graph_definition_summary()


def run_demo_graph_from_payload(
    user_id: str,
    goal_id: str,
    goal: str,
    timeline_weeks: int,
    hours_per_week: int,
    max_revisions: int,
    critic_reject_until_revision: int = 0,
    simulate_failure_node: NodeName | None = None,
) -> GraphState:
    metadata: dict[str, Any] = {
        "critic_reject_until_revision": critic_reject_until_revision,
        "phase": "phase_3_demo",
    }
    if simulate_failure_node is not None:
        metadata["simulate_failure_node"] = simulate_failure_node

    service = PathAIGraphService()
    initial_state = service.create_initial_state(
        user_id=user_id,
        goal_id=goal_id,
        goal=goal,
        timeline_weeks=timeline_weeks,
        hours_per_week=hours_per_week,
        max_revisions=max_revisions,
        metadata=metadata,
    )
    return service.run_demo_graph(initial_state)
