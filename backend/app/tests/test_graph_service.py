from app.agents.graph import build_langgraph_app
from app.agents.service import PathAIGraphService


def test_demo_graph_happy_path_completes_without_real_llm() -> None:
    service = PathAIGraphService()
    state = service.create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn LangGraph",
        timeline_weeks=8,
        hours_per_week=10,
    )

    final_state = service.run_demo_graph(state)

    assert final_state.job_status == "completed"
    assert final_state.current_stage == "completed"
    assert final_state.critic_review is not None
    assert final_state.critic_review.approved is True
    assert final_state.metadata["resource_node_called"] is True
    assert final_state.metadata["persist_placeholder"] == "no_database_write_in_phase_3"


def test_demo_graph_revision_loop_returns_to_curriculum() -> None:
    service = PathAIGraphService()
    state = service.create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn LangGraph",
        timeline_weeks=8,
        hours_per_week=10,
        metadata={"critic_reject_until_revision": 1},
    )

    final_state = service.run_demo_graph(state)
    curriculum_completions = [
        event for event in final_state.trace if event.node_name == "curriculum_node"
    ]

    assert final_state.job_status == "completed"
    assert final_state.revision_count == 1
    assert len(curriculum_completions) >= 4


def test_demo_graph_max_revision_auto_approval() -> None:
    service = PathAIGraphService()
    state = service.create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn LangGraph",
        timeline_weeks=8,
        hours_per_week=10,
        max_revisions=1,
        metadata={"critic_reject_until_revision": 5},
    )

    final_state = service.run_demo_graph(state)

    assert final_state.job_status == "completed"
    assert final_state.critic_review is not None
    assert final_state.critic_review.auto_approved is True
    assert final_state.warnings[0].code == "max_revisions_reached"


def test_demo_graph_failure_routing() -> None:
    service = PathAIGraphService()
    state = service.create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn LangGraph",
        timeline_weeks=8,
        hours_per_week=10,
        metadata={"simulate_failure_node": "resource_node"},
    )

    final_state = service.run_demo_graph(state)

    assert final_state.job_status == "failed"
    assert final_state.current_stage == "failed"
    assert final_state.errors[0].code == "simulated_node_failure"
    assert final_state.trace[-1].node_name == "failure_node"


def test_compiled_langgraph_app_runs_placeholder_flow() -> None:
    service = PathAIGraphService()
    state = service.create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn LangGraph",
        timeline_weeks=8,
        hours_per_week=10,
    )

    compiled_graph = build_langgraph_app()
    result = compiled_graph.invoke(state.model_dump(mode="json"))

    assert result["job_status"] == "completed"
    assert result["current_stage"] == "completed"
    assert result["critic_review"]["approved"] is True
