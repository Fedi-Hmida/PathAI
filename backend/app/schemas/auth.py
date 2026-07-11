from __future__ import annotations

from datetime import datetime
from typing import Annotated, TypeAlias

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampedDTO
from app.schemas.ids import UserId

# Pragmatic email check kept dependency-free (no email-validator): one "@",
# a non-empty local part, and a dotted domain. Normalization to lowercase is
# done in the service, not here.
Email: TypeAlias = Annotated[
    str,
    Field(min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
]
Password: TypeAlias = Annotated[str, Field(min_length=8, max_length=128)]


class UserCreate(BaseSchema):
    email: Email
    password: Password


class LoginRequest(BaseSchema):
    email: Email
    password: Password


class UserDTO(TimestampedDTO):
    """Public user representation. Never carries the password hash."""

    user_id: UserId
    email: Email


class UserRecord(TimestampedDTO):
    """Internal, persisted user record. Never returned by the API."""

    user_id: UserId
    email: Email
    password_hash: str = Field(min_length=1, max_length=255)

    def to_public(self) -> UserDTO:
        return UserDTO(
            user_id=self.user_id,
            email=self.email,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class RefreshTokenRecord(BaseSchema):
    """Server-side record of an issued refresh token, keyed by its jti.

    Enables rotation (revoke the old jti on refresh) and reuse detection
    (a refresh presented for an already-revoked jti revokes the whole family).
    """

    jti: str = Field(min_length=1, max_length=120)
    user_id: UserId
    revoked: bool = False
    created_at: datetime
    expires_at: datetime


class AuthSessionResponse(BaseSchema):
    """Login/register/refresh body. The refresh token travels in an httpOnly
    cookie and is intentionally absent here."""

    user: UserDTO
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(ge=1)
