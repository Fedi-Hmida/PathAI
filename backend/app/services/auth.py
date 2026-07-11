from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.core.security import (
    RefreshTokenClaims,
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.repositories.errors import NotFoundError
from app.repositories.protocols import RefreshTokenRepository, UserRepository
from app.schemas.auth import (
    AuthSessionResponse,
    LoginRequest,
    RefreshTokenRecord,
    UserCreate,
    UserDTO,
    UserRecord,
)
from app.schemas.ids import USER_PREFIX


class AuthError(Exception):
    """Base class for authentication failures. Carries no secret material."""


class EmailAlreadyRegisteredError(AuthError):
    """Raised when registering an email that already exists."""


class InvalidCredentialsError(AuthError):
    """Raised when email/password authentication fails, for either reason."""


class TokenRejectedError(AuthError):
    """Raised when an access or refresh token is invalid, expired, or reused."""


@dataclass(slots=True, frozen=True)
class AuthTokenConfig:
    secret: str
    algorithm: str
    access_ttl_seconds: int
    refresh_ttl_seconds: int


@dataclass(slots=True)
class AuthService:
    users: UserRepository
    refresh_tokens: RefreshTokenRepository
    config: AuthTokenConfig

    def register(self, payload: UserCreate) -> UserDTO:
        email = _normalize_email(payload.email)
        if self.users.find_by_email(email) is not None:
            raise EmailAlreadyRegisteredError
        now = datetime.now(tz=UTC)
        record = UserRecord(
            user_id=f"{USER_PREFIX}{uuid4().hex}",
            email=email,
            password_hash=hash_password(payload.password),
            created_at=now,
            updated_at=now,
        )
        return self.users.create(record).to_public()

    def authenticate(self, payload: LoginRequest) -> UserRecord:
        email = _normalize_email(payload.email)
        user = self.users.find_by_email(email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError
        return user

    def issue_session(self, user: UserDTO) -> tuple[AuthSessionResponse, str]:
        """Return the API body plus the raw refresh token (for the cookie)."""
        now = datetime.now(tz=UTC)
        access = create_access_token(
            subject=user.user_id,
            secret=self.config.secret,
            algorithm=self.config.algorithm,
            ttl_seconds=self.config.access_ttl_seconds,
            now=now,
        )
        jti = uuid4().hex
        refresh = create_refresh_token(
            subject=user.user_id,
            jti=jti,
            secret=self.config.secret,
            algorithm=self.config.algorithm,
            ttl_seconds=self.config.refresh_ttl_seconds,
            now=now,
        )
        self.refresh_tokens.create(
            RefreshTokenRecord(
                jti=jti,
                user_id=user.user_id,
                revoked=False,
                created_at=now,
                expires_at=now + timedelta(seconds=self.config.refresh_ttl_seconds),
            )
        )
        response = AuthSessionResponse(
            user=user,
            access_token=access,
            expires_in=self.config.access_ttl_seconds,
        )
        return response, refresh

    def rotate_session(self, refresh_token: str) -> tuple[AuthSessionResponse, str]:
        claims = self._decode_refresh(refresh_token)
        record = self.refresh_tokens.find_by_jti(claims.jti)
        if record is None:
            raise TokenRejectedError
        if record.revoked:
            # A revoked refresh token presented again means the token was
            # replayed. Revoke the whole family so a leaked token can't be used.
            self.refresh_tokens.revoke_all_for_user(record.user_id)
            raise TokenRejectedError
        self.refresh_tokens.revoke(record.jti)
        try:
            user = self.users.get_by_id(record.user_id)
        except NotFoundError as exc:
            raise TokenRejectedError from exc
        return self.issue_session(user.to_public())

    def logout(self, refresh_token: str | None) -> None:
        """Best-effort revocation. A missing or invalid token is a no-op."""
        if not refresh_token:
            return
        try:
            claims = decode_refresh_token(
                refresh_token,
                secret=self.config.secret,
                algorithm=self.config.algorithm,
            )
        except TokenError:
            return
        self.refresh_tokens.revoke(claims.jti)

    def resolve_access(self, access_token: str) -> UserDTO:
        try:
            claims = decode_access_token(
                access_token,
                secret=self.config.secret,
                algorithm=self.config.algorithm,
            )
        except TokenError as exc:
            raise TokenRejectedError from exc
        try:
            return self.users.get_by_id(claims.subject).to_public()
        except NotFoundError as exc:
            raise TokenRejectedError from exc

    def _decode_refresh(self, refresh_token: str) -> RefreshTokenClaims:
        try:
            return decode_refresh_token(
                refresh_token,
                secret=self.config.secret,
                algorithm=self.config.algorithm,
            )
        except TokenError as exc:
            raise TokenRejectedError from exc


def _normalize_email(email: str) -> str:
    return email.strip().lower()
