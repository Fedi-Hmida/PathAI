import pytest

from app.agents.checkpointing import InMemoryCheckpointStore
from app.agents.errors import CheckpointNotFoundError
from app.agents.service import PathAIGraphService


def test_checkpoint_save_and_load_latest() -> None:
    store = InMemoryCheckpointStore()
    state = PathAIGraphService().create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn LangGraph",
        timeline_weeks=8,
        hours_per_week=10,
    )

    first = store.save(state)
    state.current_stage = "started"
    second = store.save(state)
    latest = store.load_latest(state.run_id)

    assert first.sequence == 1
    assert second.sequence == 2
    assert latest.current_stage == "started"


def test_checkpoint_missing_run_raises_clear_error() -> None:
    store = InMemoryCheckpointStore()

    with pytest.raises(CheckpointNotFoundError):
        store.load_latest("missing-run")


def test_service_saves_checkpoints_during_demo_run() -> None:
    store = InMemoryCheckpointStore()
    service = PathAIGraphService(checkpoint_store=store)
    state = service.create_initial_state(
        user_id="user-1",
        goal_id="goal-1",
        goal="Learn LangGraph",
        timeline_weeks=8,
        hours_per_week=10,
    )

    final_state = service.run_demo_graph(state)

    assert final_state.job_status == "completed"
    assert len(store.list_for_run(state.run_id)) >= 7
