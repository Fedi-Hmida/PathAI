# PathAI

PathAI is a personalized learning path generator for students. The target product flow is a local no-auth demo where a learner enters a goal, completes a diagnostic assessment, receives a knowledge map and week-by-week curriculum, sees curated resources, takes quizzes, and eventually gets adaptive replanning and evaluation.

The project is currently in a disciplined rebuild. The backend foundation is implemented through Rebuild-4, with typed contracts, deterministic fixtures, fake repositories, and service skeletons in place. Full product workflows are intentionally not implemented yet.

## Architecture References

These files are the source of truth for the rebuild:

- `docs\architecture\MAIN.md`
- `docs\architecture\RULES.md`

Every phase should follow those documents unless an explicit architecture/rules update is approved.

## Current Status

Completed rebuild milestones:

- Rebuild-1B: backend dependency installation and validation recovery.
- Rebuild-2: core schemas and contracts.
- Rebuild-3 scope: deterministic mock LLM and agent fixtures, completed inside Rebuild-2 and documented in the roadmap alignment note.
- Rebuild-4: fake repositories and service skeletons.

Current backend capabilities:

- FastAPI application foundation.
- Safe settings and logging foundation.
- Health and readiness endpoints.
- Pydantic v2 product schemas and DTO contracts.
- Deterministic canonical demo fixtures.
- Mock agent output fixtures.
- Fake in-memory repositories.
- Thin service skeletons.
- Backend validation tests for the current foundation.

## Not Implemented Yet

The following are intentionally postponed:

- product API routes beyond health/readiness
- MongoDB persistence
- LangGraph workflow execution
- real LLM calls in default tests
- RAG ranking implementation
- quiz scoring logic
- adaptation execution
- frontend application
- authentication, JWT, sessions, or protected routes
- Docker, deployment, and CI/CD

## Backend Setup

From the backend folder:

```cmd
cd /d C:\Users\Fedi\Desktop\PathAI\backend
python -m pip install -e ".[dev]"
```

If a virtual environment already exists, prefer using it:

```cmd
cd /d C:\Users\Fedi\Desktop\PathAI\backend
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Backend Validation

From `backend`:

```cmd
.venv\Scripts\python.exe -m compileall app
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check app
.venv\Scripts\python.exe -m mypy app --no-incremental
.venv\Scripts\python.exe -m pytest app\tests\test_live_llm_spike_optional.py -v
```

Live LLM tests are optional and skipped by default. Do not enable `ENABLE_LIVE_LLM_TESTS` unless you intentionally want to run a configured live provider check.

## Secret Safety

Never commit real secrets. Do not read, print, copy, modify, or expose `.env`. Use `.env.example` files only for placeholders. Real API keys, MongoDB URIs, tokens, passwords, and private credentials must stay out of source code, tests, docs, fixtures, and frontend files.

## Next Phase

The next planned phase is:

```text
Rebuild-5: Backend Product API Boundary With Fake Services
```
