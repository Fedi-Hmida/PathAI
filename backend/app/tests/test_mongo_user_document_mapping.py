from __future__ import annotations

from datetime import UTC, datetime

from app.repositories.mongo.base import from_document, to_document
from app.schemas.auth import RefreshTokenRecord, UserRecord

_USER = UserRecord(
    user_id="user_mapping_test",
    email="learner@example.com",
    password_hash="argon2id$fake-hash-for-mapping-test-only",
    created_at=datetime(2026, 7, 9, 12, 0, tzinfo=UTC),
    updated_at=datetime(2026, 7, 9, 12, 0, tzinfo=UTC),
)

_REFRESH_TOKEN = RefreshTokenRecord(
    jti="jti-mapping-test",
    user_id="user_mapping_test",
    revoked=False,
    created_at=datetime(2026, 7, 9, 12, 0, tzinfo=UTC),
    expires_at=datetime(2026, 7, 23, 12, 0, tzinfo=UTC),
)


def test_user_record_document_round_trip() -> None:
    document = to_document(_USER, _USER.user_id)

    assert document["_id"] == _USER.user_id
    assert document["email"] == _USER.email
    assert isinstance(document["created_at"], str)
    # The stored document must carry the hash (needed to verify logins) but
    # the public schema layer (UserDTO) is a separate type that never does.
    assert document["password_hash"] == _USER.password_hash

    restored = from_document(document, UserRecord)
    assert restored == _USER


def test_user_record_to_public_omits_password_hash() -> None:
    public = _USER.to_public()

    assert public.user_id == _USER.user_id
    assert public.email == _USER.email
    assert not hasattr(public, "password_hash")


def test_refresh_token_record_document_round_trip() -> None:
    document = to_document(_REFRESH_TOKEN, _REFRESH_TOKEN.jti)

    assert document["_id"] == _REFRESH_TOKEN.jti
    assert document["user_id"] == _REFRESH_TOKEN.user_id
    assert document["revoked"] is False

    restored = from_document(document, RefreshTokenRecord)
    assert restored == _REFRESH_TOKEN
