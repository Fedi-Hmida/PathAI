# Runtime Config vs. Code Defaults

**Status:** Reference note (Rebuild-38 / Big_Audit Step 1).

## The distinction

`app/core/settings.py`'s `Settings` uses `env_file=None` — it never reads `.env` itself, only real
process env vars. In isolation (e.g. under pytest, or a bare `uvicorn app.main:app`), every setting
falls back to its code default: `repository_backend="fake"`, `llm_mock_mode=True`, all
`enable_llm_*_agent` flags `False`, `enable_auth=False`.

`make api` runs `backend/scripts/run_dev.py`, which loads the repo-root `.env` (untracked) into
`os.environ` **before** starting uvicorn in-process (`load_env_file`, `os.environ.setdefault`), then
sets `PATHAI_ENABLE_AUTH=true` as a local-dev default if `.env` didn't already set it. Because
`Settings` reads whatever is in `os.environ` at process start, the *running* dev app is configured by
`.env`, not by the code defaults above.

## What the dev runtime actually is

Per the current root `.env` (values not reproduced here — see the redacted inventory below):

- `REPOSITORY_BACKEND=mongo` — Mongo/Atlas is the live backend, not `fake`.
- `LLM_PROVIDER=groq`, `LLM_MOCK_MODE=false` — real provider calls, not the mock client.
- `PATHAI_ENABLE_LLM_ASSESSMENT_AGENT`, `PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT`,
  `PATHAI_ENABLE_LLM_CURRICULUM_AGENT` all `true` — three LLM agents active simultaneously. This exact
  combination is on the validated allowlist (`app/agents/services/activation/allowlist.py`); critic
  stays deterministic (its flag is unset/`false`).
- `PATHAI_ENABLE_AUTH=true` (via `run_dev.py`'s default) — accounts required.

So `make api` serves a Mongo(Atlas)-backed, Groq-backed, 3-LLM-agent, auth-on app — not the
fake/mock/no-agents/no-auth posture the code defaults alone would suggest.

## Why the pytest suite still looks "all off"

The default test suite never runs `run_dev.py` and never loads `.env`, so every test process sees
only the code defaults: `fake` repositories, mock LLM client, all LLM-agent flags off, auth off. This
is why `pytest` is deterministic and requires no network, LLM, or MongoDB by default (`RULES.md`
§14). Opt-in live suites (`test_live_mongo_*_optional.py`, `test_live_llm_spike_optional.py`) load
`.env`/set flags explicitly and are skipped otherwise.

## Redacted `.env` key inventory (names + roles only — never values for secrets)

| Key | Role | Secret? |
|---|---|---|
| `MONGODB_URI` | Atlas connection string | **secret — never print** |
| `MONGODB_DATABASE_NAME` | target DB name (dev value: `pathai_dev`) | not secret |
| `REPOSITORY_BACKEND` | `fake` \| `mongo` (dev: `mongo`) | not secret |
| `MONGODB_CONNECT_ON_STARTUP` | connect at process startup (dev: `true`) | not secret |
| `JWT_SECRET_KEY` | JWT signing secret | **secret — never print** |
| `LLM_PROVIDER` | active provider id (dev: `groq`) | not secret |
| `LLM_MOCK_MODE` | mock vs real LLM client (dev: `false`) | not secret |
| `LLM_BASE_URL` / `OPENAI_BASE_URL` / `UNIVERSITY_LLM_API_URL` | provider base URL | not secret (URL, not a credential) |
| `LLM_API_KEY` / `OPENAI_API_KEY` / `UNIVERSITY_LLM_API_KEY` | provider API key | **secret — never print** |
| `LLM_MODEL` / `UNIVERSITY_LLM_MODEL` | model id | not secret |
| `PATHAI_ENABLE_LLM_ASSESSMENT_AGENT` | per-agent LLM gate (dev: `true`) | not secret |
| `PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT` | per-agent LLM gate (dev: `true`) | not secret |
| `PATHAI_ENABLE_LLM_CURRICULUM_AGENT` | per-agent LLM gate (dev: `true`) | not secret |
| `PATHAI_ENABLE_LLM_CRITIC_AGENT` | per-agent LLM gate (dev: unset → `false`) | not secret |
| `TAVILY_API_KEY` | search provider key (currently unset) | **secret — never print** |
| `LANGSMITH_API_KEY` | tracing provider key (currently unset) | **secret — never print** |
| `SENDGRID_API_KEY` | email provider key (currently unset) | **secret — never print** |
| `SENTRY_DSN` | error-tracking DSN (currently unset) | **secret — never print** |
| `PATHAI_ENABLE_AUTH` | accounts required (`run_dev.py` defaults `true` if unset in `.env`) | not secret |

Anything matching `secret|token|key|password|uri` (case-insensitive) is redacted by
`Settings.redacted_dict()` in health/readiness output — the same rule applies here: state
presence/config, never the value.
