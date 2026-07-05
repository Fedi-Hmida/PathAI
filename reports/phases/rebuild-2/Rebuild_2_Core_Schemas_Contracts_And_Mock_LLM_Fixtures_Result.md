# Rebuild-2 Core Schemas, Contracts, And Mock LLM Fixtures Result

Status: Completed  
Project: PathAI  
Phase: Rebuild-2  
Created: 2026-07-05  

## A. Scope

This phase implemented Rebuild-2 typed backend contracts, deterministic canonical demo fixtures, deterministic mock agent output fixtures, and validation/security tests.

The work stayed limited to schemas, fixtures, tests, and this result recap. It did not implement PathAI product workflow behavior.

## Roadmap Alignment Note

This phase implemented the canonical `Rebuild-2: Core Schemas And Contracts` scope plus the mock-fixture scope originally listed in `docs\architecture\MAIN.md` as `Rebuild-3: Mock LLM And Deterministic Agent Fixtures`.

The canonical Rebuild-3 mock fixture work is therefore considered completed as part of this result.

The next phase should be named according to `MAIN.md`:

```text
Rebuild-4: Fake Repositories And Service Skeleton
```

## B. MAIN.md / RULES.md Compliance

This phase followed:

- `docs\architecture\MAIN.md`
- `docs\architecture\RULES.md`
- `reports\phases\rebuild-2\Rebuild_2_Core_Schemas_Contracts_And_Mock_LLM_Fixtures_Action_Plan.md`

Compliance decisions:

- Used typed Pydantic v2 contracts and explicit DTOs.
- Split schemas by domain instead of using one giant schema file.
- Kept Rebuild-1 LLM spike schemas separate from product schemas.
- Kept fixtures deterministic and mock-first.
- Treated fixture and mock agent output as untrusted until validated by tests.
- Did not implement services, repositories, MongoDB persistence, LangGraph execution, product API routes, frontend, authentication, Docker, deployment, live LLM calls, network calls, or product workflow logic.
- Did not access `.env`.

## C. Files Created or Updated

Created:

- `backend\app\schemas\base.py`
- `backend\app\schemas\ids.py`
- `backend\app\schemas\enums.py`
- `backend\app\schemas\goal.py`
- `backend\app\schemas\assessment.py`
- `backend\app\schemas\knowledge_map.py`
- `backend\app\schemas\curriculum.py`
- `backend\app\schemas\resource.py`
- `backend\app\schemas\progress.py`
- `backend\app\schemas\quiz.py`
- `backend\app\schemas\adaptation.py`
- `backend\app\schemas\critic.py`
- `backend\app\schemas\evaluation.py`
- `backend\app\schemas\orchestration.py`
- `backend\app\schemas\dashboard.py`
- `backend\app\fixtures\__init__.py`
- `backend\app\fixtures\canonical_demo.py`
- `backend\app\fixtures\mock_agents.py`
- `backend\app\tests\test_schema_imports.py`
- `backend\app\tests\test_schema_validation.py`
- `backend\app\tests\test_demo_fixtures_validate.py`
- `backend\app\tests\test_mock_agent_fixtures_validate.py`
- `backend\app\tests\test_schema_security.py`
- `reports\phases\rebuild-2\Rebuild_2_Core_Schemas_Contracts_And_Mock_LLM_Fixtures_Result.md`

Preserved:

- `backend\app\schemas\llm_spike.py`

## D. Work Completed

Shared contracts:

- Added base schema configuration with forbidden extra fields.
- Added timestamp, version, trace, workflow error, workflow warning, and normalized score primitives.
- Added opaque ID aliases with prefix validation for all `MAIN.md` ID prefixes.
- Added string-valued enums for statuses and controlled vocabularies.

Domain contracts:

- Added goal, learner profile, assessment, knowledge map, curriculum, resource, progress, quiz, adaptation, critic, evaluation, orchestration, and dashboard schemas.
- Added structured agent input/output contracts for assessment, knowledge map, curriculum, resource, quiz, adaptation, critic, and evaluation.
- Added lightweight workflow state and orchestration DTOs without graph execution.
- Added dashboard payload read-model schemas without frontend logic.

Fixtures:

- Added deterministic canonical demo fixtures for the RAG graduation-project path.
- Added deterministic mock agent outputs that validate against agent output schemas.
- Kept fixtures free of LLM calls, network calls, MongoDB calls, and workflow execution.

Tests:

- Added schema import tests.
- Added schema validation tests for valid payloads, invalid statuses, invalid score ranges, invalid ID prefixes, extra fields, and curriculum duration consistency.
- Added canonical demo fixture validation and ID-link consistency tests.
- Added mock agent fixture validation tests.
- Added fixture security tests for secret-like strings and forbidden environment/external-client references.

## E. Validation Commands And Results

Commands run from `C:\Users\Fedi\Desktop\PathAI\backend` using `.venv\Scripts\python.exe`:

```cmd
.venv\Scripts\python.exe -m compileall app
```

Result: Passed.

```cmd
.venv\Scripts\python.exe -m pytest
```

Result: Passed.

- 30 passed
- 3 skipped
- 2 warnings

Warnings:

- `StarletteDeprecationWarning` from the FastAPI/TestClient dependency stack.
- `PytestCacheWarning` for `.pytest_cache` cache path creation.

```cmd
.venv\Scripts\python.exe -m ruff check app
```

Result: Passed.

- `All checks passed!`

```cmd
.venv\Scripts\python.exe -m mypy app --no-incremental
```

Result: Passed.

- `Success: no issues found in 55 source files`

```cmd
.venv\Scripts\python.exe -m pytest app\tests\test_live_llm_spike_optional.py -v
```

Result: Passed with all optional live LLM tests skipped.

- 3 skipped
- 1 warning

## F. Security / Secret Handling

- `.env` was not read, printed, copied, modified, or exposed.
- No secrets, API keys, MongoDB URIs, tokens, passwords, private keys, credentials, or private config were added.
- Fixtures contain deterministic demo data only.
- Fixture security tests scan public fixture values for secret-like strings.
- No live LLM call was made.
- `ENABLE_LIVE_LLM_TESTS` was not enabled.
- No network call was made.
- No MongoDB call was made.
- No frontend code was changed.

## G. Mock LLM / Fixture Result

Implemented:

- Canonical demo fixtures for goal, learner profile, assessment, knowledge map, curriculum, resources, progress, quiz, quiz attempt, adaptation event, critic review, evaluation report, and dashboard payload.
- Mock agent outputs for:
  - Assessment Agent
  - Assessment scoring
  - Knowledge Map Agent
  - Curriculum Agent
  - Resource/RAG Agent
  - Critic Agent
  - Quiz Agent
  - Quiz scoring
  - Adapter/Replanning Agent
  - Evaluation Agent

Validation result:

- Canonical demo fixtures validate against product schemas.
- Mock agent fixtures validate against agent output schemas.
- Fixture ID links are consistent in tests.
- Fixture data aligns with the canonical RAG graduation-project goal.

## H. Not Done / Intentionally Postponed

Intentionally not implemented:

- Business services.
- Repository interfaces or implementations.
- Product API routes beyond existing health/readiness.
- MongoDB models.
- MongoDB connections.
- MongoDB persistence.
- MongoDB integration tests.
- LangGraph graph execution.
- Real LLM calls.
- Live LLM behavior changes.
- RAG ranking implementation.
- Quiz scoring implementation.
- Adaptation execution.
- Progress mutation logic.
- Evaluation scoring implementation.
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
- Product workflow execution.

## I. Remaining Risks

- The fixture corpus is intentionally small and is not the final RAG seed corpus acceptance set.
- Schema constraints may need tightening or relaxing when services and repositories exercise them in later phases.
- Cross-domain schema imports should be watched in later phases to avoid circular dependencies as behavior is added.
- The current validation environment uses Python 3.14.5; future dependency behavior should be rechecked if the Python version changes.
- Non-blocking warnings remain from the FastAPI/TestClient dependency stack and pytest cache handling.

## J. Next Recommended Phase

Proceed next to:

```text
Rebuild-4: Fake Repositories And Service Skeleton
```

This next phase should use the Rebuild-2 schemas and fixtures without adding MongoDB, live LLM calls, frontend, authentication, Docker, deployment, or production workflow scope.
