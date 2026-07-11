from __future__ import annotations


class TokenError(Exception):
    """Raised when a JWT is missing, malformed, expired, or has wrong claims.

    Carries no token material and no provider detail so it is safe to log and
    to surface as a generic authentication failure.
    """
