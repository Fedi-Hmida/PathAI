from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error, InvalidHashError, VerifyMismatchError

# Argon2id with library defaults; a single shared hasher is safe to reuse.
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return an Argon2id hash string for the given plaintext password."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Return True when the plaintext password matches the stored hash.

    Never raises on a wrong password or a malformed stored hash; both are
    reported as a non-match so callers can return a single generic error.
    """
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError, Argon2Error):
        return False
