from __future__ import annotations

from app.repositories.fakes.base import InMemoryStore
from app.schemas.auth import UserRecord
from app.schemas.ids import UserId


class FakeUserRepository:
    def __init__(self) -> None:
        self._users: InMemoryStore[UserRecord] = InMemoryStore("user")

    def create(self, user: UserRecord) -> UserRecord:
        return self._users.create(user.user_id, user)

    def get_by_id(self, user_id: UserId) -> UserRecord:
        return self._users.get(user_id)

    def find_by_email(self, email: str) -> UserRecord | None:
        matches = self._users.list_where("email", email)
        return matches[0] if matches else None

    def clear(self) -> None:
        self._users.clear()
