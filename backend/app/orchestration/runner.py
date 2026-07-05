from __future__ import annotations

from dataclasses import dataclass

from app.fixtures import canonical_demo as demo
from app.orchestration.graph import build_straight_line_graph
from app.orchestration.nodes import OrchestrationContext, ServiceContainerProtocol
from app.orchestration.state import (
    build_initial_workflow_state,
    graph_state_to_workflow_state,
    workflow_state_to_graph_state,
)
from app.schemas.enums import ExecutionMode
from app.schemas.ids import GoalId, RunId
from app.schemas.orchestration import OrchestrationRunDTO, WorkflowState


@dataclass(slots=True)
class OrchestrationRunResult:
    state: WorkflowState
    run: OrchestrationRunDTO


def run_straight_line_demo(
    context: OrchestrationContext,
    *,
    run_id: RunId = demo.RUN_ID,
    goal_id: GoalId = demo.GOAL_ID,
) -> OrchestrationRunResult:
    initial_state = build_initial_workflow_state(
        run_id=run_id,
        goal_id=goal_id,
        mode=ExecutionMode.DEMO,
        created_at=demo.NOW,
    )
    graph = build_straight_line_graph(context)
    final_graph_state = graph.invoke(workflow_state_to_graph_state(initial_state))
    final_state = graph_state_to_workflow_state(final_graph_state)
    return OrchestrationRunResult(
        state=final_state,
        run=context.orchestration_runs.get_by_id(run_id),
    )


def run_straight_line_demo_from_container(
    container: ServiceContainerProtocol,
    *,
    run_id: RunId = demo.RUN_ID,
    goal_id: GoalId = demo.GOAL_ID,
) -> OrchestrationRunResult:
    return run_straight_line_demo(
        OrchestrationContext.from_container(container),
        run_id=run_id,
        goal_id=goal_id,
    )
