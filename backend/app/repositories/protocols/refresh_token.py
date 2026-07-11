from __future__ import annotations

from typing import Protocol

from app.schemas.auth import RefreshTokenRecord
from app.schemas.ids import UserId


class RefreshTokenRepository(Protocol):
    def create(self, record: RefreshTokenRecord) -> RefreshTokenRecord: ...

    def find_by_jti(self, jti: str) -> RefreshTokenRecord | None: ...

    def revoke(self, jti: str) -> None: ...

    def revoke_all_for_user(self, user_id: UserId) -> None: ...

    def clear(self) -> None: ...
