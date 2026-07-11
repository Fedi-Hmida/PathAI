from __future__ import annotations

from app.repositories.fakes.base import InMemoryStore
from app.schemas.auth import RefreshTokenRecord
from app.schemas.ids import UserId


class FakeRefreshTokenRepository:
    def __init__(self) -> None:
        self._tokens: InMemoryStore[RefreshTokenRecord] = InMemoryStore("refresh token")

    def create(self, record: RefreshTokenRecord) -> RefreshTokenRecord:
        return self._tokens.create(record.jti, record)

    def find_by_jti(self, jti: str) -> RefreshTokenRecord | None:
        matches = self._tokens.list_where("jti", jti)
        return matches[0] if matches else None

    def revoke(self, jti: str) -> None:
        if self.find_by_jti(jti) is not None:
            self._tokens.update_fields(jti, revoked=True)

    def revoke_all_for_user(self, user_id: UserId) -> None:
        for record in self._tokens.list_where("user_id", user_id):
            if not record.revoked:
                self._tokens.update_fields(record.jti, revoked=True)

    def clear(self) -> None:
        self._tokens.clear()
