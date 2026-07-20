"""Standalone, opt-in, purge-only reset of platform data (Mongo backend only).

Purges every document from all 13 repositories via their existing `.clear()`
method (`delete_many({})` per collection) -- schema, validators, and indexes
are left untouched. Never re-seeds fixtures (does not call
`load_canonical_demo()`). Deliberately not wired into any HTTP route,
FastAPI dependency, Makefile target, or startup path (RULES.md §15) --
invoke manually:

    backend\\.venv\\Scripts\\python.exe scripts\\reset_platform_data.py

Three checks run in order, none skippable, before any database write:
  1. Hard denylist on the resolved database name (`MONGODB_DATABASE_NAME`).
  2. An explicit confirmation env var (`PATHAI_CONFIRM_RESET`) that must
     equal the resolved database name exactly.
  3. `repository_backend` must be `"mongo"` -- this tool targets the live
     backend only; purging `fake` in-memory repos is meaningless outside a
     running process.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.run_dev import load_env_file  # noqa: E402

_DENYLIST = frozenset({"pathai", "pathai_prod", "prod", "production"})
_CONFIRM_ENV_VAR = "PATHAI_CONFIRM_RESET"

# Mirrors ApiServiceContainer.clear() (app/api/v1/dependencies.py) -- the
# same 13 repositories, purge-only, no fixture re-seed.
REPOSITORY_FIELD_NAMES = (
    "goal",
    "assessment",
    "knowledge_map",
    "curriculum",
    "resource",
    "progress",
    "quiz",
    "adaptation",
    "critic",
    "evaluation",
    "orchestration_run",
    "user",
    "refresh_token",
)


class ResetRefused(Exception):
    """Raised by a safety check that refuses to proceed; message is printable as-is."""


def _check_not_denylisted(database_name: str) -> None:
    if database_name.strip().lower() in _DENYLIST:
        msg = (
            f"database name {database_name!r} is on the hard denylist "
            f"({sorted(_DENYLIST)}); this safeguard cannot be bypassed"
        )
        raise ResetRefused(msg)


def _check_confirmation_token(database_name: str) -> None:
    confirmation = os.environ.get(_CONFIRM_ENV_VAR)
    if not confirmation or confirmation != database_name:
        msg = (
            f"set {_CONFIRM_ENV_VAR}=<database name> to confirm "
            "(must exactly match the configured database name)"
        )
        raise ResetRefused(msg)


def _check_mongo_backend(repository_backend: str) -> None:
    if repository_backend.strip().lower() != "mongo":
        msg = (
            f"repository_backend is {repository_backend!r}; this script only "
            "targets 'mongo' (purging the fake backend outside a running process "
            "is meaningless)"
        )
        raise ResetRefused(msg)


def run_safety_checks(database_name: str, repository_backend: str) -> None:
    """Run all refusal checks, in order. Raises ResetRefused on the first failure."""
    _check_not_denylisted(database_name)
    _check_confirmation_token(database_name)
    _check_mongo_backend(repository_backend)


def purge_all(repositories: object) -> list[str]:
    """Call .clear() on every repository field. Returns the field names cleared, in order."""
    cleared: list[str] = []
    for field_name in REPOSITORY_FIELD_NAMES:
        repo = getattr(repositories, field_name)
        repo.clear()
        cleared.append(field_name)
    return cleared


def main() -> None:
    load_env_file(ENV_FILE)

    from app.core.settings import get_settings
    from app.repositories.factory import build_repository_set

    settings = get_settings()

    try:
        run_safety_checks(settings.mongodb_database_name, settings.repository_backend)
    except ResetRefused as exc:
        print(f"Refusing to reset: {exc}", file=sys.stderr)
        sys.exit(1)

    repositories = build_repository_set(settings)
    cleared = purge_all(repositories)

    print(
        f"Purged {len(cleared)} repositories in database "
        f"{settings.mongodb_database_name!r}: {', '.join(cleared)}",
    )


if __name__ == "__main__":
    main()
