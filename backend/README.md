# PathAI Backend

Status: implemented through Rebuild-4.

The backend currently provides the local no-auth demo foundation. It includes FastAPI app setup, safe configuration boundaries, health/readiness endpoints, typed product contracts, deterministic fixtures, fake repositories, and thin service skeletons.

It does not yet run the full PathAI product workflow.

## Implemented

- FastAPI application skeleton.
- Settings and logging foundation.
- Secret-safe health and readiness endpoints.
- Structured-output LLM spike interfaces.
- Mock LLM client and mock structured-output tests.
- Pydantic v2 schemas for goals, assessments, knowledge maps, curricula, resources, progress, quizzes, adaptation, critic reviews, evaluation, orchestration, and dashboard payloads.
- Deterministic canonical demo fixtures.
- Deterministic mock agent output fixtures.
- Fake in-memory repositories with deep-copy isolation.
- Repository protocols and repository errors.
- Thin service skeletons with constructor-injected repositories.
- Read-only dashboard service composition from repository DTOs.

## Not Implemented Yet

The following are intentionally out of scope at the current rebuild stage:

- product API routes beyond health/readiness
- MongoDB repositories or database connections
- Beanie, Motor, or PyMongo integration
- LangGraph graph execution
- real LLM calls in default tests
- agent runtime implementation
- RAG ranking algorithms
- quiz scoring logic
- adaptation execution
- evaluation formulas
- frontend implementation
- authentication, JWT, sessions, or protected routes
- Docker, deployment, and CI/CD

## Install

From `backend`:

```cmd
python -m pip install -e ".[dev]"
```

If the backend virtual environment already exists:

```cmd
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Run

From `backend`:

```cmd
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Health endpoints:

```text
GET /api/v1/health
GET /api/v1/readiness
```

Health/readiness responses must not expose secrets, connection strings, API keys, or raw config values.

## Validation

From `backend`:

```cmd
.venv\Scripts\python.exe -m compileall app
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check app
.venv\Scripts\python.exe -m mypy app --no-incremental
.venv\Scripts\python.exe -m pytest app\tests\test_live_llm_spike_optional.py -v
```

Default tests do not require a live LLM, network, MongoDB, Docker, or frontend dependencies.

## LLM Spike

Default tests use mock LLM behavior only. Live LLM checks are optional, manual, and skipped by default.

Do not enable `ENABLE_LIVE_LLM_TESTS` unless you intentionally want to run a configured live provider check. Do not print or expose `.env`. Do not commit real credentials. `.env.example` contains placeholders only.
