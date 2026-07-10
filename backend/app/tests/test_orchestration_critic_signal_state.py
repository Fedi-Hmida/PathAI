from __future__ import annotations

from app.api.v1.dependencies import ApiServiceContainer
from app.orchestration.graph import MAX_CRITIC_REVISION_ATTEMPTS
from app.orchestration.nodes import OrchestrationContext
from app.orchestration.runner import run_straight_line_demo
from app.orchestration.state import build_initial_workflow_state
from app.schemas.enums import CriticPassStatus, OrchestrationStatus
from app.schemas.ids import GoalId, RunId


def test_initial_state_seeds_inert_critic_signal_fields() -> None:
    state = build_initial_workflow_state(
        run_id=RunId("run_seed"),
        goal_id=GoalId("goal_seed"),
    )
    assert state.critic_pass_status is None
    assert state.critic_recommendations == []
    # Rebuild-23A's cap primitive is present but not yet load-bearing.
    assert MAX_CRITIC_REVISION_ATTEMPTS == 1


def test_load_critic_review_populates_pass_status_and_recommendations() -> None:
    container = ApiServiceContainer()
    context = OrchestrationContext.from_container(container)

    result = run_straight_line_demo(context)

    assert result.state.status == OrchestrationStatus.COMPLETED
    # load_critic_review now surfaces the critic's categorical signal into
    # lightweight graph state (Rebuild-23A) — this is what should_revise_curriculum
    # will route on in 23C, but nothing routes on it yet.
    assert isinstance(result.state.critic_pass_status, CriticPassStatus)
    assert isinstance(result.state.critic_recommendations, list)
    assert len(result.state.critic_recommendations) <= 10
