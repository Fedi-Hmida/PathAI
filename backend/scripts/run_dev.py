"""Local dev entrypoint for `make api`.

Loads the repo-root `.env` (untracked, real local credentials) into the
process environment, then starts uvicorn in-process. Deliberately does not
`source .env` in a shell first: on Git Bash/MSYS, values that look like a
POSIX absolute path (e.g. `API_V1_PREFIX=/api/v1`) get silently rewritten to
a Windows path (`C:/Program Files/Git/api/v1`) when handed to a native
Windows process via a shell subprocess. Setting `os.environ` directly here
and starting uvicorn in the same process avoids that translation layer
entirely.
"""

from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env"


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def main() -> None:
    load_env_file(ENV_FILE)
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
