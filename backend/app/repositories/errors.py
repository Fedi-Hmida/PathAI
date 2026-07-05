from __future__ import annotations


class RepositoryError(Exception):
    """Base error for repository boundary failures."""


class NotFoundError(RepositoryError):
    """Raised when a requested repository record does not exist."""


class DuplicateRecordError(RepositoryError):
    """Raised when creating a record whose ID already exists."""
