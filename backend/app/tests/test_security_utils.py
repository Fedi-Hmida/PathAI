from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)

SECRET = "unit-test-secret-value-not-real-0123456789"


def test_hash_password_round_trip_and_rejects_wrong_password() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert verify_password("correct horse battery staple", password_hash)
    assert not verify_password("wrong password", password_hash)


def test_hash_password_never_stores_plaintext() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert "correct horse battery staple" not in password_hash


def test_verify_password_returns_false_for_malformed_stored_hash() -> None:
    assert not verify_password("anything", "not-a-real-argon2-hash")


def test_access_token_round_trips_subject() -> None:
    token = create_access_token(
        subject="user_abc123",
        secret=SECRET,
        algorithm="HS256",
        ttl_seconds=900,
    )

    claims = decode_access_token(token, secret=SECRET, algorithm="HS256")

    assert claims.subject == "user_abc123"


def test_access_token_rejects_wrong_secret() -> None:
    token = create_access_token(
        subject="user_abc123",
        secret=SECRET,
        algorithm="HS256",
        ttl_seconds=900,
    )

    with pytest.raises(TokenError):
        decode_access_token(
            token,
            secret="a-different-secret-value-also-0123456789",
            algorithm="HS256",
        )


def test_access_token_rejects_expired_token() -> None:
    issued_in_the_past = datetime.now(tz=UTC) - timedelta(hours=1)
    token = create_access_token(
        subject="user_abc123",
        secret=SECRET,
        algorithm="HS256",
        ttl_seconds=60,
        now=issued_in_the_past,
    )

    with pytest.raises(TokenError):
        decode_access_token(token, secret=SECRET, algorithm="HS256")


def test_refresh_token_round_trips_subject_and_jti() -> None:
    token = create_refresh_token(
        subject="user_abc123",
        jti="jti-001",
        secret=SECRET,
        algorithm="HS256",
        ttl_seconds=1000,
    )

    claims = decode_refresh_token(token, secret=SECRET, algorithm="HS256")

    assert claims.subject == "user_abc123"
    assert claims.jti == "jti-001"


def test_access_token_cannot_be_decoded_as_refresh_token() -> None:
    access = create_access_token(
        subject="user_abc123",
        secret=SECRET,
        algorithm="HS256",
        ttl_seconds=900,
    )

    with pytest.raises(TokenError):
        decode_refresh_token(access, secret=SECRET, algorithm="HS256")


def test_refresh_token_cannot_be_decoded_as_access_token() -> None:
    refresh = create_refresh_token(
        subject="user_abc123",
        jti="jti-001",
        secret=SECRET,
        algorithm="HS256",
        ttl_seconds=900,
    )

    with pytest.raises(TokenError):
        decode_access_token(refresh, secret=SECRET, algorithm="HS256")


def test_decode_rejects_tampered_token() -> None:
    token = create_access_token(
        subject="user_abc123",
        secret=SECRET,
        algorithm="HS256",
        ttl_seconds=900,
    )
    # Flip a character in the middle of the signature segment. Flipping the
    # very last character is unreliable: base64url padding bits can be
    # redundant, so the decoded signature bytes (and thus verification)
    # sometimes don't change.
    midpoint = len(token) // 2
    flipped = "A" if token[midpoint] != "A" else "B"
    tampered = token[:midpoint] + flipped + token[midpoint + 1 :]

    with pytest.raises(TokenError):
        decode_access_token(tampered, secret=SECRET, algorithm="HS256")
