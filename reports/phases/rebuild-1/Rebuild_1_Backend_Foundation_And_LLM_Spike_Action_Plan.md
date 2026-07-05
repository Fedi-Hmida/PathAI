# Rebuild-1 Backend Foundation And LLM Spike Action Plan

Status: Planning document  
Project: PathAI  
Phase: Rebuild-1  
Created: 2026-06-23  

## A. Phase Objective

Rebuild-1 establishes the backend project foundation, developer tooling, safe configuration layer, minimal FastAPI application skeleton, safe health/readiness surface, logging foundation, and an isolated LLM structured-output spike plan.

The phase must make the backend ready for later schema, service, repository, orchestration, and agent work. It must not implement product business workflows.

Rebuild-1 success means:

- The backend can be started locally after dependencies are installed.
- The backend has a small FastAPI app skeleton.
- The backend has a safe settings layer that does not expose secrets.
- The backend has safe health/readiness endpoints if implemented.
- The backend has test/lint/type-check tooling configured.
- Default tests do not require a live LLM, network, MongoDB Atlas, or secrets.
- The LLM structured-output spike is isolated, optional, manual/environment-gated, and never required by default tests.
- A Rebuild-1 result recap documents validation, security handling, and remaining risks.

## B. MAIN.md / RULES.md Alignment

This action plan was prepared after reviewing:

- `docs\architecture\MAIN.md`
- `docs\architecture\RULES.md`

Rebuild-1 is governed by these MAIN.md decisions:

- Rebuild-1 is "Backend Project Foundation, Tooling, And LLM Spike".
- Rebuild-1 should set up FastAPI, Pytest, and verify whether the university-hosted LLM can handle JSON schemas.
- Rebuild-1 must not implement product or business workflow logic.
- Authentication, Docker, deployment, production hosting, CI/CD, live web scraping, and production multi-user logic remain postponed.
- Default tests must not depend on real LLM calls.
- The first target remains a local no-auth demo.

Rebuild-1 is governed by these RULES.md restrictions:

- Read and respect `MAIN.md` and `RULES.md`.
- Keep changes scoped to the requested phase.
- Do not implement future phases early.
- Keep files small and cohesive.
- Separate API routes, services, settings, logging, schemas, LLM helpers, and tests.
- API routes stay thin.
- Business logic belongs in services, but business workflow logic is out of scope for Rebuild-1.
- Preserve `.env`; never read, print, copy, modify, or expose secrets.
- Use mock LLM clients in tests.
- No default tests should require real LLM, network, or MongoDB.
- Validate with real commands and report exact results.
- Create a result recap under `reports\phases`.

## C. Scope

In scope for Rebuild-1 implementation:

- Backend packaging/tooling foundation.
- Minimal FastAPI app skeleton.
- Settings/config layer.
- Logging foundation.
- Safe error response foundation if needed.
- Health endpoint.
- Readiness endpoint if it reports only safe configured/unconfigured flags.
- Local backend README updates.
- Pytest setup.
- Ruff setup.
- Mypy setup.
- Security-safe environment variable handling.
- `.env.example` with placeholders only, if not already present.
- Mock/test-safe settings.
- Isolated LLM client interface/spike module.
- Mock LLM structured-output test.
- Optional live LLM spike script/test marked manual and skipped by default.
- Validation command documentation.
- Rebuild-1 result recap.

## D. Out Of Scope

Out of scope for Rebuild-1 implementation:

- Frontend code.
- Authentication.
- JWT.
- Login/register.
- Password hashing.
- Sessions.
- Protected routes.
- Docker.
- Deployment.
- CI/CD.
- Business workflow endpoints.
- Assessment logic.
- Knowledge-map generation logic.
- Curriculum generation logic.
- RAG/resource ranking logic.
- Critic review logic.
- Progress tracking logic.
- Quiz generation/scoring logic.
- Adaptation/replanning logic.
- Evaluation scoring logic.
- MongoDB Atlas persistence implementation.
- Repository implementations beyond minimal placeholders if needed for import stability.
- LangGraph workflow implementation.
- Live web scraping.
- Advanced vector infrastructure.
- Any default test that requires network, MongoDB, live LLM, or secrets.

## E. Existing Project Structure Review

Observed current structure:

```text
backend/
  README.md
  app/
    __init__.py
    agents/
    api/
      __init__.py
      v1/
        __init__.py
    core/
      __init__.py
    db/
      __init__.py
    evaluation/
      __init__.py
    models/
      __init__.py
    orchestration/
      __init__.py
    rag/
      __init__.py
    repositories/
      __init__.py
    schemas/
      __init__.py
    services/
      __init__.py
    tests/
      __init__.py
    utils/
      __init__.py
```

The backend is currently a scaffold:

- Folder boundaries already match the clean architecture direction in `MAIN.md`.
- `backend\README.md` exists but is empty.
- `backend\app\__init__.py` and package `__init__.py` files exist.
- No backend runtime foundation files are present yet.
- No backend dependency/tooling files are present yet.
- No product business logic is present.

Implication for Rebuild-1:

- Use the existing scaffold.
- Do not reorganize the architecture.
- Add only minimal foundation files needed for backend startup, settings, health/readiness, tooling, tests, and LLM spike isolation.

## F. Proposed Backend Foundation Structure

Recommended Rebuild-1 files/modules:

```text
backend/
  pyproject.toml
  README.md
  .env.example
  app/
    main.py
    api/
      v1/
        router.py
        health.py
    core/
      settings.py
      logging.py
      errors.py
    llm/
      __init__.py
      client.py
      mock_client.py
      structured_output_spike.py
    schemas/
      llm_spike.py
    tests/
      test_app_import.py
      test_health.py
      test_readiness.py
      test_settings_safety.py
      test_mock_llm_structured_output.py
      test_live_llm_spike_optional.py
```

Notes:

- `backend\pyproject.toml` is preferred over scattered requirements files for tool configuration and dependency groups.
- `backend\app\main.py` should stay small and primarily create/configure the FastAPI app.
- `backend\app\api\v1\router.py` should aggregate routers.
- `backend\app\api\v1\health.py` should contain health/readiness routes only.
- `backend\app\core\settings.py` should define safe settings and redaction behavior.
- `backend\app\core\logging.py` should define safe logging setup.
- `backend\app\core\errors.py` may define basic safe error shapes if needed.
- `backend\app\llm\client.py` should define the LLM client protocol/interface only.
- `backend\app\llm\mock_client.py` should return deterministic mock structured outputs.
- `backend\app\llm\structured_output_spike.py` should be optional/manual and environment-gated.
- `backend\app\schemas\llm_spike.py` should contain tiny test schemas for the spike only, not full product schemas.
- Test files should remain small and focused.

Do not create assessment, curriculum, RAG, critic, progress, quiz, adaptation, evaluation, MongoDB, or LangGraph business modules in Rebuild-1.

## G. Dependency Strategy

Recommended runtime dependencies:

| Dependency | Why Needed |
|---|---|
| `fastapi` | Backend API framework. |
| `uvicorn[standard]` | Local ASGI server for development. |
| `pydantic` | Typed DTOs and structured-output validation. |
| `pydantic-settings` | Safe settings layer from environment variables. |
| `httpx` | Test client support and optional future LLM HTTP client. |

Recommended development dependencies:

| Dependency | Why Needed |
|---|---|
| `pytest` | Backend test runner. |
| `pytest-asyncio` | Async test support for future client and LLM tests. |
| `ruff` | Linting and import/style checks. |
| `mypy` | Static type checking. |
| `types-*` packages | Only if mypy requires them later. |

Optional live LLM dependency strategy:

- Prefer `httpx` for provider-agnostic HTTP calls if the university LLM exposes an HTTP endpoint.
- Do not add a provider-specific SDK until the provider interface is known.
- Keep live LLM dependency optional and isolated.

Do not install dependencies during this planning task.

## H. Settings And Secret Handling Plan

Settings goals:

- Load configuration only through `backend\app\core\settings.py`.
- Avoid direct `os.environ` reads across the codebase.
- Never print loaded secret values.
- Provide safe redacted representation for logging/debugging.
- Make live LLM settings optional and disabled by default.

Recommended settings fields:

```text
APP_NAME=PathAI
APP_ENV=local
APP_DEBUG=false
API_V1_PREFIX=/api/v1
BACKEND_CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
LLM_PROVIDER=mock
LLM_BASE_URL=
LLM_MODEL=
LLM_API_KEY=
LLM_TIMEOUT_SECONDS=45
ENABLE_LIVE_LLM_TESTS=false
```

`.env` handling:

- Preserve the existing private `.env`.
- Do not read, print, copy, modify, or expose `.env` contents.
- Runtime settings may support environment variables, but validation and tests must not require real secret values.
- `.env.example` should include placeholder names only, never real credentials.

Readiness behavior:

- Readiness may report `llm_configured: true/false`.
- Readiness must not return `LLM_API_KEY`, `LLM_BASE_URL`, MongoDB URI, or any secret-like value.
- Readiness may report provider name only if it is non-sensitive.

Test behavior:

- Tests should monkeypatch environment variables or instantiate settings directly with safe dummy values.
- Tests must not require `.env`.
- Tests must verify secret-like values are redacted from settings representation and readiness output.

## I. FastAPI Foundation Plan

Recommended approach:

- Use `backend\app\main.py` with a small `create_app()` factory and exported `app`.
- Configure app title/version from safe settings.
- Include `api\v1\router.py`.
- Keep `main.py` small and free of business workflow logic.

API router:

- `backend\app\api\v1\router.py` creates one `APIRouter`.
- It includes `health.py`.
- No product workflow routers yet.

Health endpoint:

```text
GET /api/v1/health
```

Allowed response:

```json
{
  "status": "ok",
  "service": "PathAI",
  "environment": "local"
}
```

Readiness endpoint:

```text
GET /api/v1/readiness
```

Allowed response:

```json
{
  "status": "ready",
  "checks": {
    "settings_loaded": true,
    "llm_provider": "mock",
    "live_llm_enabled": false
  }
}
```

Forbidden readiness output:

- API keys.
- MongoDB URIs.
- connection strings.
- passwords.
- full request headers.
- stack traces.

CORS:

- Use local-development scoped origins first.
- Do not configure wildcard production policy.
- Keep CORS in app setup or a small helper.

Error response strategy:

- Add sanitized error response foundation only if needed.
- Do not expose stack traces.
- Keep detailed debug logs server-side and secret-redacted.

No business workflow endpoints:

- Do not add assessment, curriculum, RAG, quiz, progress, adaptation, evaluation, or orchestration endpoints in Rebuild-1.

## J. Logging And Observability Plan

Logging goals:

- Safe local debugging.
- No secret leakage.
- Future request/run trace readiness.
- Small, understandable implementation.

Recommended behavior:

- Configure logging in `backend\app\core\logging.py`.
- Use structured fields where practical: timestamp, level, logger, message, request_id, run_id if present.
- Prepare for `request_id` propagation later without implementing full middleware if not needed.
- Do not log full request headers.
- Do not log authorization values, API keys, `.env` values, MongoDB URIs, or provider secrets.
- Use sanitized exception messages for API responses.

Rebuild-1 should not overbuild observability:

- No production observability stack.
- No tracing vendor.
- No metrics backend.
- No log aggregation.

## K. LLM Structured-Output Spike Plan

Purpose:

- Test whether the university-hosted/configurable LLM can reliably return strict JSON matching simple Pydantic schemas.
- Identify whether JSON mode, function calling, or parser/repair logic is needed later.
- Keep this spike isolated from product agents.

Minimal schemas to test:

```text
MiniKnowledgeMapOutput
- concepts: list of { concept_id, label, mastery_score, classification }
- summary: str

MiniCurriculumOutput
- title: str
- weeks: list of { week_number, theme, topics }

MiniQuizOutput
- questions: list of { prompt, options, correct_answer, concept_ids }
```

Default mock behavior:

- Mock LLM returns deterministic valid objects.
- Mock structured-output parsing is covered by default tests.
- Mock tests do not require network or secrets.

Optional live behavior:

- Live test is skipped unless `ENABLE_LIVE_LLM_TESTS=true`.
- Live test requires provider settings to be configured through environment variables.
- Live test must not print secrets.
- Live test should use a short prompt with no sensitive data.
- Live test should write only sanitized capability results to console/report.

Timeout/retry/parsing expectations:

- Use `LLM_TIMEOUT_SECONDS`, default `45`.
- Retry transient timeout/network errors only if implemented.
- Validate response against Pydantic schema.
- On schema failure, record sanitized parse error.
- Do not save invalid output.
- Do not treat LLM output as trusted.

Success means:

- Mock structured-output tests pass.
- Optional live test, if enabled, shows whether strict structured output works.
- Result recap records one of:
  - `not_run_optional`
  - `passed_live_structured_output`
  - `failed_live_structured_output`
  - `provider_not_configured`

Failure does not block default Rebuild-1 if:

- Mock path passes.
- Failure is documented honestly.
- Later phases can proceed with mock contracts and decide parser/repair strategy.

## L. Testing Strategy For Rebuild-1

Required default tests:

- App imports successfully.
- `create_app()` returns a FastAPI app.
- Health endpoint returns safe `ok` payload.
- Readiness endpoint returns safe configured/unconfigured flags.
- Readiness does not include secret-like values.
- Settings object redacts secret fields.
- Mock LLM returns valid structured output.
- Mock LLM malformed output path fails validation safely if included.
- Optional live LLM test is skipped unless explicitly enabled.

Test constraints:

- No default test reads `.env`.
- No default test requires real LLM.
- No default test requires real network.
- No default test requires MongoDB Atlas.
- No default test requires frontend.
- No default test requires Docker.

Recommended tests:

```text
backend\app\tests\test_app_import.py
backend\app\tests\test_health.py
backend\app\tests\test_readiness.py
backend\app\tests\test_settings_safety.py
backend\app\tests\test_mock_llm_structured_output.py
backend\app\tests\test_live_llm_spike_optional.py
```

## M. Validation Commands

Commands to run during the future implementation phase after dependencies are installed:

```powershell
cd backend
python -m compileall app
python -m pytest
python -m ruff check app
python -m mypy app --no-incremental
```

Optional local server smoke command:

```powershell
cd backend
python -m uvicorn app.main:app --reload
```

Optional manual LLM spike command, only when explicitly configured:

```powershell
cd backend
$env:ENABLE_LIVE_LLM_TESTS="true"
python -m pytest app/tests/test_live_llm_spike_optional.py -m live_llm
```

Validation reporting rules:

- Report exact command outcomes.
- Do not claim tests passed if dependencies are missing.
- If mypy/ruff are not configured yet, say exactly why.
- If live LLM spike is skipped, report it as skipped, not passed.

## N. File Size And Modularity Rules For This Phase

Rebuild-1 implementation must follow these modularity rules:

- No giant files.
- Each file has one clear responsibility.
- `main.py` only creates/configures the app.
- `health.py` only contains health/readiness routes.
- `settings.py` only handles configuration.
- `logging.py` only handles logging setup.
- LLM interface, mock client, and live spike code are separate.
- Tests are split by behavior.
- No business workflow logic inside foundation files.
- No assessment/curriculum/RAG/quiz/adaptation/evaluation logic.
- No duplicated contracts across unrelated files.

## O. Security Checklist

Rebuild-1 implementation must satisfy:

- `.env` not read, printed, copied, modified, or exposed by implementation work.
- `.env.example` secret-free.
- No real credentials in code, tests, docs, fixtures, or README.
- Settings representation redacts secret-like fields.
- Health endpoint returns status only, no secrets.
- Readiness endpoint returns configured/unconfigured flags only, no secret values.
- Logs redact secrets.
- No full request headers logged.
- No backend stack traces returned to clients.
- Optional live LLM test is environment-gated.
- Default tests do not require real secrets.
- No frontend exposure of backend config.
- No authentication/JWT/session work.
- No Docker/deployment work.

## P. Done Criteria

Rebuild-1 implementation is complete when:

- `MAIN.md` and `RULES.md` compliance is documented in the result recap.
- Backend dependency/tooling file exists.
- Backend README explains local backend foundation usage.
- FastAPI app skeleton exists.
- Health endpoint works.
- Readiness endpoint works and does not expose secrets.
- Settings layer exists with safe redaction.
- Logging foundation exists and avoids secrets.
- LLM client interface exists.
- Mock LLM structured-output path exists and is tested.
- Optional live LLM spike is present but skipped by default.
- Default tests pass without network, MongoDB, LLM, or secrets.
- `compileall`, `pytest`, `ruff`, and `mypy` results are reported.
- Rebuild-1 result recap is created.
- No business workflow logic was implemented.

## Q. Risks And Mitigations

| Risk | Impact | Mitigation |
|---|---:|---|
| Dependency installation failure | Medium | Keep dependencies minimal; report exact install/tooling errors. |
| Windows environment issues | Medium | Use cross-platform Python commands; avoid shell-specific assumptions where possible. |
| LLM endpoint unavailable | Medium | Keep live LLM spike optional and skipped by default. |
| Structured output unsupported | High | Document failure; continue with mock path and plan parser/repair in later phase. |
| Accidental secret exposure | High | Never print settings values; redact secrets; avoid `.env` access. |
| Scope creep into business logic | High | Restrict Rebuild-1 to foundation, health/readiness, settings, logging, LLM spike interface. |
| Oversized foundation files | Medium | Split app, router, settings, logging, LLM, schemas, and tests. |
| Default tests accidentally require network | High | Mark live tests explicitly and skip unless enabled. |
| Readiness leaks config values | High | Return only boolean/configured flags and non-sensitive provider names. |

## R. Required Rebuild-1 Result Recap Structure

The implementation phase must create:

```text
reports\phases\Rebuild_1_Backend_Foundation_And_LLM_Spike_Result.md
```

It must contain:

```text
A. Scope
B. MAIN.md / RULES.md Compliance
C. Files Created or Updated
D. Work Completed
E. Validation Commands And Results
F. Security / Secret Handling
G. LLM Spike Result
H. Not Done / Intentionally Postponed
I. Remaining Risks
J. Next Recommended Phase
```

The recap must report exact validation commands and outcomes. It must explicitly state that `.env` content was not read, printed, copied, modified, or exposed.

## S. Recommended Implementation Sequence

Recommended future implementation order:

1. Re-read `docs\architecture\MAIN.md` and `docs\architecture\RULES.md`.
2. Create/update backend dependency/tooling configuration.
3. Update `backend\README.md` with local backend foundation instructions.
4. Create `backend\.env.example` with placeholders only.
5. Implement `backend\app\core\settings.py` with safe settings and redaction.
6. Implement `backend\app\core\logging.py` with secret-safe logging setup.
7. Implement minimal `backend\app\main.py` with `create_app()`.
8. Implement `backend\app\api\v1\router.py`.
9. Implement `backend\app\api\v1\health.py` with health/readiness only.
10. Implement LLM interface and mock client in an isolated LLM module.
11. Implement tiny LLM spike schemas.
12. Add default tests for app import, health, readiness, settings safety, and mock structured output.
13. Add optional live LLM spike test marked skipped unless enabled.
14. Run validation commands.
15. Fix foundation/tooling issues only.
16. Create Rebuild-1 result recap with exact validation outcomes.

Do not add product workflow endpoints or business logic during any step.

## T. Final Recommendation

Rebuild-1 implementation should begin after this plan is accepted.

The implementation should stay tightly scoped to backend foundation, tooling, safe settings/logging, health/readiness, and the optional LLM structured-output spike. It should not implement PathAI business workflows yet.
