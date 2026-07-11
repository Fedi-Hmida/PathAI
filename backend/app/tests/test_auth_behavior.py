from __future__ import annotations

import pytest

from app.repositories.fakes import FakeRefreshTokenRepository, FakeUserRepository
from app.schemas.auth import LoginRequest, UserCreate
from app.services.auth import (
    AuthService,
    AuthTokenConfig,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    TokenRejectedError,
)

CONFIG = AuthTokenConfig(
    secret="behavior-test-secret-value-0123456789",
    algorithm="HS256",
    access_ttl_seconds=900,
    refresh_ttl_seconds=1_209_600,
)


def _service() -> AuthService:
    return AuthService(
        users=FakeUserRepository(),
        refresh_tokens=FakeRefreshTokenRepository(),
        config=CONFIG,
    )


def test_register_creates_user_without_exposing_password_hash() -> None:
    service = _service()

    user = service.register(UserCreate(email="Learner@Example.com", password="correcthorsebattery"))

    assert user.user_id.startswith("user_")
    assert user.email == "learner@example.com"
    assert not hasattr(user, "password_hash")


def test_register_rejects_duplicate_email_case_insensitively() -> None:
    service = _service()
    service.register(UserCreate(email="learner@example.com", password="correcthorsebattery"))

    with pytest.raises(EmailAlreadyRegisteredError):
        service.register(UserCreate(email="Learner@example.com", password="anotherpassword1"))


def test_authenticate_accepts_correct_credentials() -> None:
    service = _service()
    service.register(UserCreate(email="learner@example.com", password="correcthorsebattery"))

    user = service.authenticate(
        LoginRequest(email="learner@example.com", password="correcthorsebattery"),
    )

    assert user.email == "learner@example.com"


def test_authenticate_rejects_wrong_password() -> None:
    service = _service()
    service.register(UserCreate(email="learner@example.com", password="correcthorsebattery"))

    with pytest.raises(InvalidCredentialsError):
        service.authenticate(LoginRequest(email="learner@example.com", password="wrong-password"))


def test_authenticate_rejects_unknown_email() -> None:
    service = _service()

    with pytest.raises(InvalidCredentialsError):
        service.authenticate(LoginRequest(email="nobody@example.com", password="whatever12345"))


def test_issue_session_returns_access_token_and_sets_up_refresh_record() -> None:
    service = _service()
    user = service.register(UserCreate(email="learner@example.com", password="correcthorsebattery"))

    response, refresh_token = service.issue_session(user)

    assert response.access_token
    assert response.user.user_id == user.user_id
    assert refresh_token
    resolved = service.resolve_access(response.access_token)
    assert resolved.user_id == user.user_id


def test_rotate_session_issues_new_tokens_and_revokes_the_old_one() -> None:
    service = _service()
    user = service.register(UserCreate(email="learner@example.com", password="correcthorsebattery"))
    _, refresh_token = service.issue_session(user)

    response, new_refresh_token = service.rotate_session(refresh_token)

    assert response.user.user_id == user.user_id
    assert new_refresh_token != refresh_token
    with pytest.raises(TokenRejectedError):
        service.rotate_session(refresh_token)


def test_rotate_session_reuse_of_revoked_token_revokes_the_whole_family() -> None:
    service = _service()
    user = service.register(UserCreate(email="learner@example.com", password="correcthorsebattery"))
    _, refresh_token = service.issue_session(user)
    _, rotated_refresh_token = service.rotate_session(refresh_token)

    # Replaying the now-revoked original token is treated as a reuse/leak
    # signal: the entire token family (including the freshly rotated one)
    # must die, not just the replayed token.
    with pytest.raises(TokenRejectedError):
        service.rotate_session(refresh_token)

    with pytest.raises(TokenRejectedError):
        service.rotate_session(rotated_refresh_token)


def test_logout_revokes_refresh_token() -> None:
    service = _service()
    user = service.register(UserCreate(email="learner@example.com", password="correcthorsebattery"))
    _, refresh_token = service.issue_session(user)

    service.logout(refresh_token)

    with pytest.raises(TokenRejectedError):
        service.rotate_session(refresh_token)


def test_logout_is_a_no_op_for_missing_or_invalid_token() -> None:
    service = _service()

    service.logout(None)
    service.logout("not-a-real-token")


def test_resolve_access_rejects_tampered_or_foreign_token() -> None:
    service = _service()
    other_config = AuthTokenConfig(
        secret="a-completely-different-secret-9999999999",
        algorithm="HS256",
        access_ttl_seconds=900,
        refresh_ttl_seconds=1_209_600,
    )
    other_service = AuthService(
        users=FakeUserRepository(),
        refresh_tokens=FakeRefreshTokenRepository(),
        config=other_config,
    )
    user = other_service.register(
        UserCreate(email="learner@example.com", password="correcthorsebattery"),
    )
    foreign_response, _ = other_service.issue_session(user)

    with pytest.raises(TokenRejectedError):
        service.resolve_access(foreign_response.access_token)
