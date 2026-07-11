from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.core.security.errors import TokenError

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


@dataclass(slots=True, frozen=True)
class AccessTokenClaims:
    subject: str
    expires_at: datetime


@dataclass(slots=True, frozen=True)
class RefreshTokenClaims:
    subject: str
    jti: str
    expires_at: datetime


def create_access_token(
    *,
    subject: str,
    secret: str,
    algorithm: str,
    ttl_seconds: int,
    now: datetime | None = None,
) -> str:
    issued_at = now or datetime.now(tz=UTC)
    payload = {
        "sub": subject,
        "type": ACCESS_TOKEN_TYPE,
        "iat": issued_at,
        "exp": issued_at + timedelta(seconds=ttl_seconds),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def create_refresh_token(
    *,
    subject: str,
    jti: str,
    secret: str,
    algorithm: str,
    ttl_seconds: int,
    now: datetime | None = None,
) -> str:
    issued_at = now or datetime.now(tz=UTC)
    payload = {
        "sub": subject,
        "jti": jti,
        "type": REFRESH_TOKEN_TYPE,
        "iat": issued_at,
        "exp": issued_at + timedelta(seconds=ttl_seconds),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_access_token(token: str, *, secret: str, algorithm: str) -> AccessTokenClaims:
    payload = _decode(token, secret=secret, algorithm=algorithm, expected_type=ACCESS_TOKEN_TYPE)
    return AccessTokenClaims(
        subject=_require_str(payload, "sub"),
        expires_at=_expires_at(payload),
    )


def decode_refresh_token(token: str, *, secret: str, algorithm: str) -> RefreshTokenClaims:
    payload = _decode(token, secret=secret, algorithm=algorithm, expected_type=REFRESH_TOKEN_TYPE)
    return RefreshTokenClaims(
        subject=_require_str(payload, "sub"),
        jti=_require_str(payload, "jti"),
        expires_at=_expires_at(payload),
    )


def _decode(
    token: str,
    *,
    secret: str,
    algorithm: str,
    expected_type: str,
) -> dict[str, object]:
    try:
        payload: dict[str, object] = jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError("invalid token") from exc
    if payload.get("type") != expected_type:
        raise TokenError("unexpected token type")
    return payload


def _require_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise TokenError(f"missing claim: {key}")
    return value


def _expires_at(payload: dict[str, object]) -> datetime:
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)):
        raise TokenError("missing claim: exp")
    return datetime.fromtimestamp(exp, tz=UTC)
