# Rebuild-5 Backend Product API Boundary With Fake Services Action Plan

Status: Action plan  
Project: PathAI  
Phase: Rebuild-5  
Created: 2026-07-05  

## A. Phase Objective

Rebuild-5 should expose the first clean no-auth backend product API boundary for PathAI using the existing Rebuild-2 schemas, deterministic fixtures, Rebuild-4 fake repositories, and service skeletons.

The phase should answer:

- What backend API routes will the future frontend call?
- How do route handlers call services without touching repositories directly?
- How do we expose deterministic fake-backed product data safely?
- How do we keep API route files thin and modular?
- How do we prepare for later LangGraph, MongoDB, and real LLM phases without implementing them early?

This phase matters because PathAI now has contracts, fixtures, fake repositories, and service skeletons, but only health/readiness routes are exposed. Rebuild-5 should create the HTTP boundary that proves the service layer can be consumed through FastAPI while preserving clean architecture.

## B. MAIN.md / RULES.md Alignment

This phase is governed by:

- `docs\architecture\MAIN.md`
- `docs\architecture\RULES.md`
- `reports\phases\Phase_Roadmap_Alignment_Note.md`
- `reports\phases\rebuild-4\Rebuild_4_Fake_Repositories_And_Service_Skeleton_Result.md`

Relevant rules and decisions:

- The frontend talks only to the backend API.
- Backend API routes call services.
- API routes must stay thin and should only validate request boundaries, map HTTP requests to service calls, and return response DTOs.
- Services own business logic and application decisions.
- Repositories own persistence abstraction.
- Fake repositories come before Mongo-backed repositories.
- Agents must not write persistence.
- Routes must not call MongoDB drivers.
- Routes must not call LLM clients.
- Routes must not construct prompts.
- Services and repositories must remain testable with fake repositories.
- Default tests must not require real LLM, network, MongoDB, Docker, frontend, or secrets.
- Local no-auth mode is development/demo mode, not production security.
- No authentication, JWT, Docker, deployment, or CI/CD should be implemented.
- `.env` must not be read, printed, copied, modified, or exposed.
- Files should stay small, focused, and separated by responsibility.

Important roadmap note:

`MAIN.md` contains historical roadmap wording around Rebuild-5 and LangGraph. The current approved phase target is taken from the Rebuild-4 result and this task: **Rebuild-5: Backend Product API Boundary With Fake Services**. This phase must not implement LangGraph execution.

## C. Current Starting Point

Current state:

- Backend foundation is green.
- FastAPI app setup exists.
- Settings and logging foundation exist.
- Health and readiness routes exist.
- Rebuild-2 schemas/contracts are complete.
- Rebuild-2 deterministic fixtures and mock agent fixtures are complete.
- Rebuild-4 fake repositories are complete.
- Rebuild-4 service skeletons are complete.
- Dashboard service can compose a read-only dashboard payload from fake repositories.
- Validation is green in the latest Rebuild-4 and pre-push cleanup reports.
- `backend\app\api\v1\router.py` currently includes only `health.router`.
- No product API routes exist yet.
- No MongoDB connection exists.
- No Mongo-backed repositories exist.
- No LangGraph execution exists.
- No real LLM behavior has been used.
- No frontend implementation is in scope.

## D. In Scope

Allowed Rebuild-5 work:

- Product API router modules.
- Route DTO usage from existing schemas.
- Fake-backed service wiring.
- A small in-memory dependency container or factory for fake repositories and services.
- No-auth local API endpoints.
- Deterministic demo fixture loading endpoint.
- Dashboard payload endpoint backed by fake services.
- Orchestration run read/status endpoints backed by fake data.
- API error mapping for repository errors.
- Route tests using FastAPI TestClient.
- Endpoint contract tests.
- Scope/security tests for forbidden imports and `.env` references.
- Rebuild-5 result recap.

## E. Out Of Scope

Explicitly excluded:

- MongoDB repositories.
- Beanie, Motor, PyMongo, or database connections.
- Production persistence.
- LangGraph graph execution.
- Agents or agent runtime implementation.
- Real LLM calls.
- RAG ranking implementation.
- Quiz scoring implementation.
- Adaptation execution.
- Evaluation formulas.
- Real orchestration workflow.
- Frontend code.
- Authentication.
- JWT/login/register.
- Password hashing.
- Sessions or protected routes.
- Docker.
- Deployment.
- CI/CD.
- `.env` access.

## F. Proposed API Route Structure

Create small route files under:

```text
backend\app\api\v1
```

Recommended route modules:

- `goal.py`
  - `POST /goals`
  - `GET /goals/{goal_id}`
- `assessment.py`
  - `GET /assessments/{assessment_id}`
- `knowledge_map.py`
  - `GET /knowledge-maps/{knowledge_map_id}`
- `curriculum.py`
  - `GET /curricula/{curriculum_id}`
- `resource.py`
  - `GET /resources/{resource_id}`
  - `GET /resources/by-curriculum/{curriculum_id}`
- `progress.py`
  - `GET /progress/{progress_id}`
- `quiz.py`
  - `GET /quizzes/{quiz_id}`
- `adaptation.py`
  - `GET /adaptations/{adaptation_id}`
- `critic.py`
  - `GET /critic-reviews/{critic_id}`
- `evaluation.py`
  - `GET /evaluations/{evaluation_id}`
- `orchestration.py`
  - `GET /orchestration/runs/{run_id}`
  - `GET /orchestration/runs/{run_id}/status`
- `dashboard.py`
  - `GET /dashboard/{run_id}`
- `demo.py`
  - `POST /demo/load-fixtures`
- `dependencies.py`
  - service container dependency functions and demo fixture loading helper
- `errors.py` or `exception_handlers.py`
  - HTTP mapping for repository/domain boundary errors if the implementation keeps error mapping separate from `dependencies.py` or `router.py`

Keep:

- `router.py` as the API v1 aggregator.
- `health.py` unchanged unless a minor import wiring update is required.

Each route file should define its own `APIRouter`, tags, typed path parameters, service dependency, and thin route handlers.

## G. Proposed Dependency Wiring

Options considered:

1. **Simple dependency provider functions in `api\v1\dependencies.py`**
   - Pros: small, explicit, easy to test, minimal `main.py` change.
   - Cons: can become too large if it mixes container setup, seeding, and every provider without discipline.

2. **Application state container initialized in `main.py`**
   - Pros: clean request-time access via `request.app.state`.
   - Cons: pushes product wiring into app startup early and may make tests more coupled to FastAPI app state.

3. **Lightweight service container module**
   - Pros: clean separation between service construction and route dependencies.
   - Cons: adds a new concept that should stay intentionally small.

Recommended Rebuild-5 approach:

- Use `backend\app\api\v1\dependencies.py` as the public API dependency layer.
- Define a small fake-backed service container class or dataclass in that file, or in a tightly scoped helper if size requires it.
- The container should own fake repository instances and constructor-injected services.
- Route handlers should depend on service provider functions, not repositories.
- Repository access may occur inside dependency/container setup only.
- Provide a reset/load canonical fixture helper for tests and the demo endpoint.
- Keep fake stores resettable and deterministic.
- Avoid modifying `main.py` unless absolutely needed.

Rules:

- No MongoDB.
- No real LLM.
- No `.env`.
- No direct repository access from route handlers.
- Services remain constructor-injected.
- Container state must be deterministic and resettable for tests.
- Avoid hidden global state where possible; if a module-level fake container is used, tests must reset it through an explicit helper.

## H. Endpoint Plan

Minimal endpoint set:

```text
POST /api/v1/goals
GET /api/v1/goals/{goal_id}
GET /api/v1/assessments/{assessment_id}
GET /api/v1/knowledge-maps/{knowledge_map_id}
GET /api/v1/curricula/{curriculum_id}
GET /api/v1/resources/{resource_id}
GET /api/v1/resources/by-curriculum/{curriculum_id}
GET /api/v1/progress/{progress_id}
GET /api/v1/quizzes/{quiz_id}
GET /api/v1/adaptations/{adaptation_id}
GET /api/v1/critic-reviews/{critic_id}
GET /api/v1/evaluations/{evaluation_id}
GET /api/v1/orchestration/runs/{run_id}
GET /api/v1/orchestration/runs/{run_id}/status
GET /api/v1/dashboard/{run_id}
POST /api/v1/demo/load-fixtures
```

Endpoint behavior:

- Endpoints expose fake-backed stored DTOs.
- Endpoints use existing schema DTOs where possible.
- Endpoints return deterministic canonical fixture data after demo fixture loading.
- Endpoints do not execute AI workflow.
- Endpoints do not generate assessments.
- Endpoints do not generate knowledge maps.
- Endpoints do not generate curricula.
- Endpoints do not attach resources through ranking.
- Endpoints do not score quizzes.
- Endpoints do not adapt curricula.
- Endpoints do not run evaluation formulas.
- Endpoints do not call LLM.
- Endpoints do not run LangGraph.

`POST /api/v1/goals`:

- Accept `LearningGoalCreate`.
- Create a fake-backed `LearningGoalDTO`.
- Use backend-generated opaque string IDs with valid prefixes.
- Use the provided learner profile if present.
- Use a safe default learner profile only if the schema requires a profile and none is supplied.
- Persist only through `GoalService`.
- Do not start assessment or orchestration.

`GET /api/v1/quizzes/{quiz_id}`:

- Should return a learner-safe quiz payload if `LearnerQuizDTO` is available and compatible.
- Must not expose hidden answer keys in learner-facing responses.
- If the existing service only returns `QuizDTO`, the implementation should map to a learner-safe DTO in a small helper, not in complex route logic.

`GET /api/v1/orchestration/runs/{run_id}/status`:

- Should return `OrchestrationStatusResponse`.
- Should map the fake `OrchestrationRunDTO.status` to frontend-oriented orchestration status using the same mapping already used by `DashboardService` or a shared small helper.

## I. Deterministic Demo Seeding Plan

Include:

```text
POST /api/v1/demo/load-fixtures
```

This endpoint should:

- Clear existing fake stores first.
- Load the canonical demo goal.
- Load the canonical orchestration run record, if needed for dashboard/status endpoints.
- Load assessment session and answers.
- Load knowledge map.
- Load curriculum.
- Load resources and resource attachments.
- Load progress state.
- Load quiz and quiz attempt.
- Load adaptation event.
- Load critic review.
- Load evaluation report.
- Return key IDs:
  - `run_id`
  - `goal_id`
  - `assessment_id`
  - `knowledge_map_id`
  - `curriculum_id`
  - `progress_id`
  - `quiz_id`
  - `quiz_attempt_id`
  - `adaptation_id`
  - `critic_id`
  - `evaluation_id`
- Optionally return `dashboard_payload` to support a one-call demo smoke test.

Rules:

- Source data must come from `backend\app\fixtures\canonical_demo.py`.
- All persisted fake data should be stored through services.
- The endpoint must be clearly labeled deterministic local demo data.
- The endpoint is not production behavior.
- The endpoint must not call agents.
- The endpoint must not call an LLM.
- The endpoint must not call network.
- The endpoint must not call MongoDB.
- The endpoint must not run LangGraph.
- The endpoint must not execute scoring, adaptation, RAG ranking, or evaluation formulas.

Tests should use this endpoint to establish deterministic state before reading product endpoints.

## J. API Error Handling Plan

Map errors consistently:

- `NotFoundError` -> HTTP 404.
- `DuplicateRecordError` -> HTTP 409.
- FastAPI/Pydantic validation errors -> HTTP 422.
- Unexpected exceptions -> sanitized HTTP 500.

Response rules:

- Do not expose stack traces.
- Do not expose raw exception internals.
- Do not expose secret values.
- Do not expose `.env` values.
- Return short, stable, frontend-safe error messages.
- Keep error mapping centralized through FastAPI exception handlers or a small route helper.

Recommended payload shape:

```json
{
  "detail": "resource not found"
}
```

Avoid adding an elaborate error schema unless it already exists or is needed by tests.

## K. Route Thinness Rules

Route handlers must:

- Accept path/body/query inputs.
- Rely on Pydantic/FastAPI validation.
- Call service methods.
- Return schema DTOs or small response wrappers.
- Map errors through centralized error handling.

Route handlers must not:

- Contain business workflow logic.
- Call repositories directly.
- Call MongoDB.
- Call LLM clients.
- Call agents.
- Run LangGraph.
- Construct prompts.
- Score quizzes.
- Execute adaptation.
- Rank RAG resources.
- Compute evaluation formulas.
- Mutate fixtures directly, except through a demo seeding helper/service container.
- Read or reference `.env`.

## L. Test Plan For Rebuild-5

Add focused tests under `backend\app\tests`.

Suggested test files:

- `test_api_product_routes.py`
  - imports route modules
  - loads fixtures
  - validates happy-path reads for goals, assessment, knowledge map, curriculum, resources, progress, quiz, adaptation, critic review, evaluation, and orchestration run
- `test_api_demo_seed.py`
  - confirms demo load endpoint clears and reloads deterministic fake stores
  - confirms returned IDs match canonical fixtures
  - confirms repeated calls are deterministic
- `test_api_error_mapping.py`
  - confirms missing IDs return 404
  - confirms duplicate create returns 409 where applicable
  - confirms malformed path/body input returns 422
- `test_api_dashboard.py`
  - confirms dashboard endpoint returns a valid `DashboardPayload`
  - confirms status endpoint returns lightweight polling payload
- `test_api_scope_security.py`
  - scans API route/dependency modules for forbidden imports and `.env` references
  - rejects MongoDB, Beanie, Motor, PyMongo, LangGraph execution, LLM clients, agents, network clients, frontend imports, and route-level repository calls where practical

Tests must verify:

- API router imports cleanly.
- Health/readiness still work.
- Product endpoints use fake-backed services.
- Demo seed endpoint works.
- Dashboard endpoint works.
- Orchestration status endpoint works.
- Missing records return 404.
- Duplicate records return 409 if duplicate creation is exposed.
- No live LLM tests are enabled.
- No network, MongoDB, Docker, frontend, or `.env` is required.

## M. Validation Commands

Run after implementation from:

```text
C:\Users\Fedi\Desktop\PathAI\backend
```

Commands:

```cmd
.venv\Scripts\python.exe -m compileall app
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check app
.venv\Scripts\python.exe -m mypy app --no-incremental
.venv\Scripts\python.exe -m pytest app\tests\test_live_llm_spike_optional.py -v
```

Expected:

- compile passes
- default tests pass
- Ruff passes
- mypy passes
- optional live LLM tests remain skipped by default

Do not enable `ENABLE_LIVE_LLM_TESTS`.

## N. File Size And Modularity Rules

Implementation should follow these constraints:

- No giant API route file.
- Split routes by domain.
- Keep dependency wiring small.
- Split container helpers if `dependencies.py` grows too large.
- Keep error mapping separate if that improves clarity.
- Avoid circular imports.
- Avoid global hidden state where possible.
- If module-level fake state is used, expose an explicit reset/load helper.
- Do not hide MongoDB logic behind fake service names.
- Do not add product workflow orchestration.
- Do not call LLM.
- Do not add frontend-specific formatting inside backend routes.
- Keep route tests focused and readable.

## O. Security Checklist

Before Rebuild-5 is complete, confirm:

- No `.env` access.
- No `.env` content read, printed, copied, modified, or exposed.
- No secrets in API responses.
- No API keys.
- No tokens.
- No passwords.
- No MongoDB URI.
- No private credentials.
- No real LLM calls.
- No network calls.
- No MongoDB calls.
- No frontend exposure of backend internals.
- No stack traces in HTTP responses.
- No auth/JWT/session implementation.
- Local no-auth mode is clearly development/demo only.
- Demo data is deterministic and safe.
- `.env.example` remains placeholder-only.

## P. Done Criteria

Rebuild-5 is complete only when:

- Product API routers exist.
- `router.py` aggregates product routers.
- Health/readiness still work.
- Endpoints use services.
- Route handlers do not call repositories directly.
- Fake-backed services are wired safely.
- Demo fixture load endpoint works if included.
- Dashboard endpoint works if included.
- Orchestration run/status endpoints work if included.
- API error mapping works.
- Route/API tests pass.
- Scope/security tests pass.
- Validation commands pass.
- Optional live LLM tests remain skipped by default.
- No MongoDB, real LLM, LangGraph execution, network, frontend, auth, Docker, deployment, or CI/CD is implemented.
- Result recap is created.

## Q. Risks And Mitigations

Risks:

- Routes become business logic.
- Fake global state leaks between tests.
- Endpoint set becomes too large.
- API contracts drift from schemas.
- Frontend assumptions are added too early.
- Demo seed endpoint is mistaken for production behavior.
- Hidden dependency on fixtures makes later production wiring harder.
- Route tests become brittle.
- Error responses leak internals.
- `dependencies.py` becomes a large catch-all file.

Mitigations:

- Keep route handlers as service-call adapters.
- Add explicit fake container reset/load behavior.
- Keep Rebuild-5 endpoint set read-heavy and minimal.
- Use existing schema DTOs.
- Add scope/security tests.
- Label demo endpoint as deterministic local demo data.
- Keep fixture loading isolated in one helper.
- Use stable canonical fixture IDs in tests.
- Centralize error mapping.
- Split dependency/container code if it grows beyond a small focused file.

## R. Required Rebuild-5 Result Recap Structure

Implementation must create:

```text
C:\Users\Fedi\Desktop\PathAI\reports\phases\rebuild-5\Rebuild_5_Backend_Product_API_Boundary_With_Fake_Services_Result.md
```

The recap must include:

```text
A. Scope
B. MAIN.md / RULES.md Compliance
C. Files Created or Updated
D. Work Completed
E. Validation Commands And Results
F. Security / Secret Handling
G. API Boundary Result
H. Not Done / Intentionally Postponed
I. Remaining Risks
J. Next Recommended Phase
```

The recap must honestly report exact validation output, warnings, and anything intentionally postponed.

## S. Recommended Implementation Sequence

1. Re-read `docs\architecture\MAIN.md` and `docs\architecture\RULES.md`.
2. Inspect existing `health.py`, `router.py`, services, fake repositories, schemas, and fixtures.
3. Design the dependency wiring/container.
4. Implement centralized API error mapping.
5. Implement route modules by domain.
6. Implement deterministic demo fixture load endpoint.
7. Update `router.py` to aggregate product route modules.
8. Add API route tests.
9. Add scope/security tests.
10. Run validation commands.
11. Fix only Rebuild-5 scoped issues.
12. Create the Rebuild-5 result recap.

## T. Final Recommendation

Rebuild-5 implementation should begin after this action plan is approved.

The implementation should remain an API boundary phase only. It should expose fake-backed product data through thin no-auth FastAPI routes and must not implement MongoDB, LangGraph execution, real LLM calls, agents, RAG ranking, quiz scoring, adaptation execution, evaluation formulas, frontend, auth, Docker, deployment, or CI/CD.
