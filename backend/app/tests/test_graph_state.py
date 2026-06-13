from app.agents.constants import DEFAULT_MAX_REVISIONS, GRAPH_VERSION
from app.agents.service import PathAIGraphService


def test_graph_state_creation_defaults() -> None:
    service = PathAIGraphService()

    state = service.create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn LangGraph orchestration",
        timeline_weeks=8,
        hours_per_week=10,
    )

    assert state.graph_version == GRAPH_VERSION
    assert state.job_status == "queued"
    assert state.current_stage == "created"
    assert state.max_revisions == DEFAULT_MAX_REVISIONS
    assert state.trace == []
    assert state.errors == []
