from __future__ import annotations

from dataclasses import dataclass

from app.repositories.errors import NotFoundError
from app.repositories.protocols.goal import GoalRepository
from app.schemas.auth import UserDTO
from app.schemas.ids import GoalId, RunId


@dataclass(slots=True)
class AuthorizationService:
    """Enforces per-user workspace ownership on reads.

    Ownership is anchored on the goal (and its run). Every workspace artifact
    carries a ``goal_id``, so access to any artifact is authorized by resolving
    its owning goal. When ``current_user`` is None (auth disabled), access is
    unrestricted — the shared no-auth demo behaves exactly as before.

    Denials raise ``NotFoundError`` (surfaced as 404) rather than a 403, so a
    caller cannot distinguish "exists but not yours" from "does not exist".
    """

    goals: GoalRepository

    def assert_goal_access(self, current_user: UserDTO | None, goal_id: GoalId) -> None:
        if current_user is None:
            return
        goal = self.goals.get_by_id(goal_id)
        if goal.owner_user_id != current_user.user_id:
            raise NotFoundError(f"goal not accessible: {goal_id}")

    def assert_run_access(self, current_user: UserDTO | None, run_id: RunId) -> None:
        if current_user is None:
            return
        goal = self.goals.get_by_run_id(run_id)
        if goal.owner_user_id != current_user.user_id:
            raise NotFoundError(f"run not accessible: {run_id}")
