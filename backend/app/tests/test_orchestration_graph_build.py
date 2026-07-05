from __future__ import annotations

from app.api.v1.dependencies import ApiServiceContainer
from app.orchestration.graph import build_straight_line_graph
from app.orchestration.nodes import NODE_SEQUENCE, OrchestrationContext


def test_straight_line_graph_builds_with_expected_node_sequence() -> None:
    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)

    graph = build_straight_line_graph(context)

    assert graph is not None
    assert NODE_SEQUENCE == (
        "initialize_run",
        "load_goal",
        "load_assessment",
        "load_knowledge_map",
        "load_curriculum",
        "load_resources",
        "load_critic_review",
        "load_progress",
        "load_quiz",
        "load_adaptation",
        "load_evaluation",
        "prepare_dashboard_payload",
        "complete_run",
    )
