# PathAI Backend

FastAPI backend for PathAI.

## Local Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

## Checks

```powershell
python -m compileall app
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check app
.\.venv\Scripts\python.exe -m mypy app --no-incremental --no-sqlite-cache --cache-dir .mypy_cache_local
```

## Current Foundation Scope

This backend currently exposes foundation and development-support endpoints:

- `GET /api/v1/health`
- `GET /api/v1/ready`
- `GET /api/v1/dev/models`
- `POST /api/v1/dev/goals/validate`
- `GET /api/v1/dev/llm/config`
- `POST /api/v1/dev/llm/mock-structured`
- `POST /api/v1/dev/llm/health-check`
- `GET /api/v1/dev/graph/definition`
- `POST /api/v1/dev/graph/demo-run`
- `POST /api/v1/dev/graph/service-backed-demo-run`
- `POST /api/v1/assessment/start`
- `GET /api/v1/assessment/{session_id}`
- `POST /api/v1/assessment/{session_id}/answer`
- `POST /api/v1/assessment/{session_id}/finalize`
- `POST /api/v1/curriculum/generate`
- `GET /api/v1/curriculum/{curriculum_id}`
- `POST /api/v1/curriculum/validate`
- `GET /api/v1/dev/curriculum/example`
- `GET /api/v1/resources/catalog/summary`
- `POST /api/v1/resources/retrieve`
- `POST /api/v1/resources/retrieve-for-curriculum`
- `POST /api/v1/resources/validate-seed`
- `GET /api/v1/dev/resources/example`
- `POST /api/v1/critic/review`
- `POST /api/v1/critic/review-curriculum`
- `GET /api/v1/critic/rubric`
- `GET /api/v1/dev/critic/example`
- `POST /api/v1/progress/initialize`
- `POST /api/v1/progress/update`
- `GET /api/v1/progress/{curriculum_id}`
- `GET /api/v1/progress/{curriculum_id}/week/{week_number}`
- `GET /api/v1/dev/progress/example`
- `POST /api/v1/quiz/generate`
- `GET /api/v1/quiz/{quiz_id}`
- `POST /api/v1/quiz/{quiz_id}/submit`
- `GET /api/v1/quiz/{curriculum_id}/history`
- `GET /api/v1/dev/quiz/example`
- `POST /api/v1/adapt/check`
- `POST /api/v1/adapt/replan`
- `GET /api/v1/adapt/{adaptation_id}`
- `GET /api/v1/adapt/{curriculum_id}/history`
- `GET /api/v1/dev/adapt/example`
- `GET /api/v1/evaluation/datasets`
- `POST /api/v1/evaluation/run-sample`
- `POST /api/v1/evaluation/learning-gain`
- `GET /api/v1/evaluation/rubrics`
- `GET /api/v1/dev/evaluation/example`

`/ready` checks MongoDB connectivity through the async Motor client. During local
development, start MongoDB through Docker Compose or point `MONGODB_URI` at a
local/Atlas development database.

Real LLM calls are disabled by default through `LLM_MOCK_MODE=true`. The
`/api/v1/dev/llm/health-check` endpoint only calls the university LLM when mock
mode is disabled and both URL/key settings are configured.

Phase 3 adds deterministic LangGraph-ready orchestration scaffolding:

- typed graph state,
- placeholder graph nodes,
- conditional routing,
- max revision control,
- failure routing,
- in-memory checkpointing,
- trace metadata,
- development graph diagnostics.

Authentication, JWT, password hashing, real agents, RAG indexing, production
feature endpoints, and real LLM calls from graph nodes are intentionally not
implemented yet.

LangGraph dependencies are declared in `requirements.txt`. The deterministic
Phase 3 graph service remains available for offline-safe tests, and
`app.agents.graph.build_langgraph_app` compiles the LangGraph-backed app when
`langgraph` is installed in the active virtual environment.

Phase 4 adds the temporary no-auth assessment system:

- goal intake validation,
- assessment session state,
- deterministic question-bank fallback,
- mock-LLM structured question generation while `LLM_MOCK_MODE=true`,
- adaptive difficulty updates,
- answer evaluation,
- knowledge map generation,
- graph-state compatibility helpers.

The assessment endpoints are intentionally no-auth/demo endpoints until the
authentication phase is implemented. They use an in-memory session store for
offline-safe development and tests. `AssessmentSessionDocument` is registered as
the future MongoDB persistence model, but live database persistence is not
required for Phase 4 tests.

Phase 5 adds the temporary no-auth curriculum generation system:

- curriculum generation from an explicit knowledge map,
- curriculum generation from a finalized in-memory assessment session,
- deterministic fallback planning for offline-safe development,
- mock-LLM structured curriculum generation while `LLM_MOCK_MODE=true`,
- week-by-week topics, subtopics, milestones, learning outcomes, and difficulty progression,
- curriculum shape validation,
- graph-state compatibility helpers.

The curriculum endpoints are intentionally no-auth/demo endpoints until the
authentication phase is implemented. They use an in-memory curriculum store for
offline-safe development and tests. `CurriculumDocument` is registered as the
future MongoDB persistence model, but live database persistence is not required
for Phase 5 tests.

Phase 6 adds the temporary no-auth Resource/RAG foundation:

- curated resource seed validation from `rag/resources/`,
- seed-to-backend resource mapping, including URL-derived `source_domain`,
- in-memory resource catalog loading,
- deterministic topic/subtopic/difficulty retrieval,
- deterministic reranking and mock-LLM structured reranking boundary,
- resource attachment to curriculum topics,
- graph-state compatibility helpers.

The Phase 6 resource endpoints are intentionally no-auth/demo endpoints until
authentication and user ownership checks exist. Tests do not require ChromaDB,
external network calls, real embedding model downloads, or real LLM calls.

Phase 7 adds the temporary no-auth Critic Agent and quality loop foundation:

- structured curriculum/resource review requests and results,
- deterministic quality rubric for curriculum pacing, prerequisites,
  difficulty progression, resource coverage, and `why_this` explanations,
- approval, rejection, and max-revision auto-approval decisions,
- actionable revision instructions for future curriculum/resource repair loops,
- mock-LLM structured critic boundary through the Phase 2 LLM layer,
- graph-state compatibility helpers for future real `critic_node` execution.

The Phase 7 critic endpoints are intentionally no-auth/demo endpoints until
authentication and user ownership checks exist. Tests do not require real LLM
calls, network access, vector databases, or persistent MongoDB writes.

Phase 8 adds the temporary no-auth Progress Tracking and Quiz System foundation:

- progress initialization from a generated curriculum,
- topic status tracking: `pending`, `in_progress`, `done`, and `stuck`,
- week and curriculum completion percentage calculation,
- progress event logging in an in-memory store,
- adapter-ready progress signals without implementing the Adapter,
- deterministic weekly quiz generation from curriculum topics,
- deterministic quiz scoring, feedback, best score, and history,
- optional mock-LLM structured quiz generation boundary,
- graph-state compatibility helpers for future Adapter inputs.

The Phase 8 progress and quiz endpoints are intentionally no-auth/demo endpoints
until authentication and user ownership checks exist. Tests do not require real
LLM calls, network access, MongoDB, or frontend dependencies.

Phase 9 adds the temporary no-auth Adapter/Replanning foundation:

- deterministic signal detection for low quiz scores, repeated stuck topics,
  behind-schedule candidates, completed weeks, ahead-of-schedule candidates,
  and manual requests,
- manual controlled replanning flow:
  `Adapter -> Curriculum -> Resource -> Critic -> Persist -> Notify`,
- conservative affected-week replanning that preserves completed weeks,
- affected-topic/week resource refresh through the Resource service,
- Critic review after replanning,
- in-memory adaptation history as the temporary persistence layer,
- notification payload creation without sending email/SMS/push,
- graph-state compatibility helpers for future production graph integration.

The Phase 9 adaptation endpoints are intentionally no-auth/demo endpoints until
authentication and user ownership checks exist. Tests do not require real LLM
calls, network access, MongoDB, a production scheduler, or real notification
providers.

Phase 10 adds the temporary no-auth Evaluation Framework:

- synthetic local learner-goal fixtures,
- deterministic metrics for assessment, curriculum, resources, critic,
  adaptation, and normalized learning gain,
- baseline definitions for static expert curriculum, single-agent LLM, and full
  PathAI,
- ablation definitions for no-RAG, no-Critic, and no-Adapter variants,
- human-review rubrics for academic/project review,
- structured and Markdown evaluation report generation.

The Phase 10 evaluation endpoints are intentionally no-auth/demo endpoints until
authentication and user ownership checks exist. Current evaluation outputs are
synthetic/offline engineering evidence only; they must not be presented as proof
of real learning effectiveness without expert review and real learner study
data.

Phase 11 adds security, privacy, and reliability hardening without implementing
authentication:

- `ENABLE_DEV_ENDPOINTS` gates `/api/v1/dev/*`.
- `ENABLE_DEMO_ENDPOINTS` gates temporary no-auth feature/demo endpoints.
- `ALLOWED_ORIGINS` configures CORS.
- `RATE_LIMIT_ENABLED` and `RATE_LIMIT_REQUESTS_PER_MINUTE` enable local/demo
  rate limiting.
- `AUDIT_LOG_ENABLED` enables redacted request audit event logging.
- `TRACE_PRIVACY_MODE` controls trace metadata sanitization.
- `EXPOSE_INTERNAL_ERRORS` controls whether unhandled exception details are
  returned to clients.

Authentication, JWTs, register/login/logout, sessions, and ownership checks are
not implemented yet. Before public deployment, disable dev endpoints, restrict
CORS, enable rate limiting, rotate credentials, and add authentication.

## RAG Resource Contract

Curated resource seed data lives under:

```text
../rag/resources/staging/
../rag/resources/approved/
```

`rag/resources/` is the canonical resource data path. The earlier action-plan
path `data/resources/` is documented only as a compatibility note and must not
be used as a second source of truth.

Resource seed JSON uses external curation field names such as
`estimated_time_minutes`, `source`, `access_label`, and `last_verified`.
Backend code maps those seed fields into the internal `ResourceDocument`
contract through `app.rag.schemas` and `app.rag.resource_loader`.

Phase 6 resource endpoint examples:

```powershell
Invoke-RestMethod http://localhost:8000/api/v1/resources/catalog/summary
Invoke-RestMethod http://localhost:8000/api/v1/dev/resources/example
```

## Development Endpoint Safety

All `/api/v1/dev/*` endpoints are local-development diagnostics only. They must
be disabled, protected, or removed before any public deployment.

Current assessment, curriculum, resource, critic, progress, quiz, and adaptation
routes are also temporary no-auth/demo routes. Production must add
authentication, ownership checks, CORS restrictions, rate limits, and credential
rotation before exposing the API outside a controlled local environment.

## Database Settings

```env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=pathai_dev
MONGODB_SERVER_SELECTION_TIMEOUT_MS=1000
MONGODB_CONNECT_ON_STARTUP=true
```

The app starts even if MongoDB is unavailable, but `/api/v1/ready` returns `503`
with a database-specific readiness message until the connection is healthy.

## LLM Settings

```env
UNIVERSITY_LLM_API_URL=
UNIVERSITY_LLM_API_KEY=
OPENAI_BASE_URL=
OPENAI_API_KEY=
UNIVERSITY_LLM_MODEL=pathai-university-default
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_RETRY_BACKOFF_SECONDS=0.5
LLM_MOCK_MODE=true
LLM_PROMPT_VERSION=v1
```

Never commit real LLM credentials. Development diagnostics return only safe
configuration flags, not secret values.

`OPENAI_BASE_URL` / `OPENAI_API_KEY` are supported as aliases for
OpenAI-compatible university gateways. If both naming styles are present, the
`UNIVERSITY_LLM_*` values take priority.

## Security Settings

```env
ENABLE_DEV_ENDPOINTS=true
ENABLE_DEMO_ENDPOINTS=true
DEMO_MODE=true
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
RATE_LIMIT_ENABLED=false
RATE_LIMIT_REQUESTS_PER_MINUTE=120
AUDIT_LOG_ENABLED=false
REDACT_LOG_VALUES=true
EXPOSE_INTERNAL_ERRORS=true
TRACE_PRIVACY_MODE=strict
```

For production-like demos, set `ENABLE_DEV_ENDPOINTS=false`, restrict
`ALLOWED_ORIGINS`, enable rate limiting, and avoid exposing internal errors.

## P1 Local No-Auth Demo

P1 adds a service-backed local demo orchestration endpoint:

```text
POST /api/v1/dev/graph/service-backed-demo-run
```

Unlike the original placeholder graph demo, this endpoint coordinates the
implemented assessment, curriculum, resource, critic, progress, quiz, adapter,
and evaluation services. It remains a local-development diagnostic endpoint and
does not implement authentication, production persistence, Docker, deployment,
or real LLM-required behavior.

The matching frontend page is:

```text
http://localhost:3000/demo
```

See `../docs/demo/local_no_auth_demo.md` for the demo runbook.
