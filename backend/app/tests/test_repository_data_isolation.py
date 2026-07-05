from __future__ import annotations

import pytest

from app.fixtures import canonical_demo as demo
from app.repositories.errors import NotFoundError
from app.repositories.fakes import FakeGoalRepository


def test_create_deep_copies_saved_dto() -> None:
    repository = FakeGoalRepository()
    goal = demo.LEARNING_GOAL.model_copy(deep=True)

    repository.create(goal)
    goal.goal_text = "Changed outside repository"

    assert repository.get_by_id(demo.GOAL_ID).goal_text == demo.LEARNING_GOAL.goal_text


def test_get_by_id_returns_deep_copy() -> None:
    repository = FakeGoalRepository()
    repository.create(demo.LEARNING_GOAL)

    returned_goal = repository.get_by_id(demo.GOAL_ID)
    returned_goal.goal_text = "Changed returned object"

    assert repository.get_by_id(demo.GOAL_ID).goal_text == demo.LEARNING_GOAL.goal_text


def test_clear_resets_repository_instance() -> None:
    repository = FakeGoalRepository()
    repository.create(demo.LEARNING_GOAL)

    repository.clear()

    with pytest.raises(NotFoundError):
        repository.get_by_id(demo.GOAL_ID)


def test_fake_repository_instances_do_not_share_state() -> None:
    first = FakeGoalRepository()
    second = FakeGoalRepository()

    first.create(demo.LEARNING_GOAL)

    with pytest.raises(NotFoundError):
        second.get_by_id(demo.GOAL_ID)
