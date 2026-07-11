from __future__ import annotations

from typing import Any

from pymongo.collection import Collection

from app.repositories.mongo.base import MongoStore
from app.schemas.auth import UserRecord
from app.schemas.ids import UserId


class MongoUserRepository:
    def __init__(self, collection: Collection[dict[str, Any]]) -> None:
        self._users: MongoStore[UserRecord] = MongoStore(collection, UserRecord, "user")
        # Enforce email uniqueness at the database level, not only in the
        # service. create_index is idempotent, so repeated construction is safe.
        collection.create_index("email", unique=True)

    def create(self, user: UserRecord) -> UserRecord:
        return self._users.create(user.user_id, user)

    def get_by_id(self, user_id: UserId) -> UserRecord:
        return self._users.get(user_id)

    def find_by_email(self, email: str) -> UserRecord | None:
        matches = self._users.list_where("email", email)
        return matches[0] if matches else None

    def clear(self) -> None:
        self._users.clear()
