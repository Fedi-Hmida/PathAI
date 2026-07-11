from __future__ import annotations

from typing import Protocol

from app.schemas.auth import UserRecord
from app.schemas.ids import UserId


class UserRepository(Protocol):
    def create(self, user: UserRecord) -> UserRecord: ...

    def get_by_id(self, user_id: UserId) -> UserRecord: ...

    def find_by_email(self, email: str) -> UserRecord | None: ...

    def clear(self) -> None: ...
