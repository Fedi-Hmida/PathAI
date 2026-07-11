from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.fixtures import canonical_demo as demo
from app.repositories.errors import NotFoundError
from app.repositories.fakes import FakeGoalRepository
from app.schemas.auth import UserDTO
from app.services.authorization import AuthorizationService

OWNER = UserDTO(
    user_id="user_owner",
    email="owner@example.com",
    created_at=datetime(2026, 7, 11, tzinfo=UTC),
    updated_at=datetime(2026, 7, 11, tzinfo=UTC),
)
OTHER = UserDTO(
    user_id="user_other",
    email="other@example.com",
    created_at=datetime(2026, 7, 11, tzinfo=UTC),
    updated_at=datetime(2026, 7, 11, tzinfo=UTC),
)


def _service_with_owned_goal() -> AuthorizationService:
    goals = FakeGoalRepository()
    goals.create(demo.LEARNING_GOAL.model_copy(update={"owner_user_id": OWNER.user_id}))
    return AuthorizationService(goals)


def test_auth_disabled_is_a_no_op_even_for_unowned_data() -> None:
    goals = FakeGoalRepository()
    goals.create(demo.LEARNING_GOAL)  # owner_user_id is None (shared demo)
    service = AuthorizationService(goals)

    # current_user None -> no scoping, no exception.
    service.assert_goal_access(None, demo.GOAL_ID)
    service.assert_run_access(None, demo.RUN_ID)


def test_owner_can_access_own_goal_and_run() -> None:
    service = _service_with_owned_goal()

    service.assert_goal_access(OWNER, demo.GOAL_ID)
    service.assert_run_access(OWNER, demo.RUN_ID)


def test_non_owner_is_denied_with_not_found() -> None:
    service = _service_with_owned_goal()

    with pytest.raises(NotFoundError):
        service.assert_goal_access(OTHER, demo.GOAL_ID)
    with pytest.raises(NotFoundError):
        service.assert_run_access(OTHER, demo.RUN_ID)


def test_authenticated_user_cannot_access_shared_unowned_demo_data() -> None:
    goals = FakeGoalRepository()
    goals.create(demo.LEARNING_GOAL)  # owner None
    service = AuthorizationService(goals)

    # An authenticated user must not see ownerless shared demo data.
    with pytest.raises(NotFoundError):
        service.assert_goal_access(OWNER, demo.GOAL_ID)


def test_missing_goal_raises_not_found() -> None:
    service = AuthorizationService(FakeGoalRepository())

    with pytest.raises(NotFoundError):
        service.assert_goal_access(OWNER, "goal_does_not_exist")
