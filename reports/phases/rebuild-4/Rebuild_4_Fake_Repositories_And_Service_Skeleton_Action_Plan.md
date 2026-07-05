# Rebuild-4 Fake Repositories And Service Skeleton Action Plan

Status: Action plan  
Project: PathAI  
Phase: Rebuild-4  
Created: 2026-07-05  

## A. Phase Objective

Rebuild-4 establishes the backend repository/service boundary using the Rebuild-2 schemas and deterministic fixtures.

This phase matters because PathAI needs a clean persistence abstraction before MongoDB, LangGraph orchestration, real LLM calls, and product API routes are introduced. Fake repositories will let backend services and tests operate deterministically without a database, while repository protocols will allow later Mongo-backed implementations to replace the fakes behind the same interface.

Rebuild-4 should answer these architecture questions:

- How will services access stored data without depending directly on MongoDB?
- How will fake repositories support deterministic local tests?
- How will later Mongo-backed repositories replace fake repositories behind the same protocol contracts?
- How will service files stay thin now while preparing for future business logic?
- How will PathAI preserve clean architecture before LangGraph and live LLM integration?

Rebuild-4 is a boundary and skeleton phase. It is not a product workflow phase.

## B. MAIN.md / RULES.md Alignment

This phase is governed by:

- `docs\architecture\MAIN.md`
- `docs\architecture\RULES.md`
- `reports\phases\Phase_Roadmap_Alignment_Note.md`

Relevant architecture and execution rules:

- Services own business logic and application decisions.
- Repositories own persistence abstraction.
- Fake repositories should exist before Mongo-backed repositories.
- Agents must not write persistence.
- Services decide what should be persisted.
- API routes must not contain business logic.
- Repositories must not call agents, LLMs, API routes, or LangGraph.
- Repositories must not decide learning strategy.
- Product workflow behavior must remain outside this phase.
- MongoDB is not introduced in Rebuild-4.
- Real LLM calls are not introduced in Rebuild-4.
- Product API endpoints are not introduced in Rebuild-4.
- Frontend work is not introduced in Rebuild-4.
- Authentication, Docker, deployment, and CI/CD remain out of scope.
- Files must remain small, focused, typed, deterministic, and testable.
- `.env` must not be read, printed, copied, modified, or exposed.

## C. Current Starting Point

Current state after Rebuild-1B, Rebuild-2, and roadmap alignment:

- Backend foundation exists and validation is green.
- Rebuild-2 schemas and contracts are implemented under `backend\app\schemas`.
- Deterministic canonical demo fixtures and mock agent fixtures are implemented under `backend\app\fixtures`.
- Rebuild-3 fixture scope from `MAIN.md` is documented as completed inside Rebuild-2.
- `reports\phases\Phase_Roadmap_Alignment_Note.md` confirms the next canonical phase is Rebuild-4.
- Repository and service packages exist only as package shells.
- No repository protocols are implemented yet.
- No fake repositories are implemented yet.
- No service skeletons are implemented yet.
- No MongoDB integration exists.
- No LangGraph graph execution exists.
- No live LLM call has been made.
- No product workflow has been implemented.

## D. In Scope

Allowed Rebuild-4 work:

- Repository protocol/interface definitions.
- Repository error types.
- Fake in-memory repository implementations.
- Repository package organization.
- Service skeletons.
- Service package organization.
- Constructor-based service dependency wiring patterns where useful.
- Tests using fake repositories and Rebuild-2 fixtures.
- Repository reset/clear behavior for tests.
- Deep-copy data isolation behavior.
- Minimal create, save, get, list, update-status, and append-event methods where needed.
- Read-only dashboard service skeleton composition if it stays simple and deterministic.
- Rebuild-4 result recap.

## E. Out Of Scope

Explicitly excluded from Rebuild-4:

- MongoDB repositories.
- Beanie, Motor, or PyMongo integration.
- Database connections.
- Production persistence.
- Product API routes.
- LangGraph graph execution.
- Real LLM calls.
- Agent implementation.
- RAG ranking implementation.
- Quiz scoring logic.
- Adaptation execution.
- Evaluation formulas.
- Full product workflow orchestration.
- Frontend code.
- Authentication.
- JWT, login, register, password hashing, sessions, or protected routes.
- Docker.
- Deployment.
- CI/CD.
- `.env` access.

## F. Proposed Repository Structure

Recommended structure: Option 2, with domain-split protocol and fake packages.

```text
backend\app\repositories\__init__.py
backend\app\repositories\errors.py
backend\app\repositories\base.py
backend\app\repositories\protocols\__init__.py
backend\app\repositories\protocols\goal.py
backend\app\repositories\protocols\assessment.py
backend\app\repositories\protocols\knowledge_map.py
backend\app\repositories\protocols\curriculum.py
backend\app\repositories\protocols\resource.py
backend\app\repositories\protocols\progress.py
backend\app\repositories\protocols\quiz.py
backend\app\repositories\protocols\adaptation.py
backend\app\repositories\protocols\critic.py
backend\app\repositories\protocols\evaluation.py
backend\app\repositories\protocols\orchestration.py
backend\app\repositories\fakes\__init__.py
backend\app\repositories\fakes\base.py
backend\app\repositories\fakes\goal.py
backend\app\repositories\fakes\assessment.py
backend\app\repositories\fakes\knowledge_map.py
backend\app\repositories\fakes\curriculum.py
backend\app\repositories\fakes\resource.py
backend\app\repositories\fakes\progress.py
backend\app\repositories\fakes\quiz.py
backend\app\repositories\fakes\adaptation.py
backend\app\repositories\fakes\critic.py
backend\app\repositories\fakes\evaluation.py
backend\app\repositories\fakes\orchestration.py
```

Reasoning:

- Option 1 is too likely to create a giant `fake.py` file.
- Option 3 mixes stable protocol names with implementation names too early.
- Option 2 keeps interfaces, fake implementations, and shared helpers separate.
- Domain files prevent one large repository module.
- Future Mongo-backed repositories can mirror the `fakes` domain package behind the same protocols.

Repository domains to define:

- `GoalRepository`
- `AssessmentRepository`
- `KnowledgeMapRepository`
- `CurriculumRepository`
- `ResourceRepository`
- `ProgressRepository`
- `QuizRepository`
- `AdaptationRepository`
- `CriticReviewRepository`
- `EvaluationRepository`
- `OrchestrationRunRepository`

Suggested error types:

- `RepositoryError`
- `NotFoundError`
- `DuplicateRecordError`

`base.py` should contain only shared repository typing or small helper primitives if genuinely needed. Shared fake store mechanics should live in `repositories\fakes\base.py`.

## G. Proposed Service Structure

Recommended service files:

```text
backend\app\services\__init__.py
backend\app\services\goal.py
backend\app\services\assessment.py
backend\app\services\knowledge_map.py
backend\app\services\curriculum.py
backend\app\services\resource.py
backend\app\services\progress.py
backend\app\services\quiz.py
backend\app\services\adaptation.py
backend\app\services\critic.py
backend\app\services\evaluation.py
backend\app\services\orchestration_run.py
backend\app\services\dashboard.py
```

Service skeletons should expose simple boundary methods only:

- Save or create a complete DTO.
- Get by ID.
- List by `goal_id`, `run_id`, `curriculum_id`, or another existing parent ID where appropriate.
- Update status only when the repository protocol supports a simple status update.
- Append orchestration node events only through the orchestration run repository.
- Compose a dashboard payload read model only from already stored DTOs, if included.

Service constructors should accept repository protocols. Services should not instantiate fake repositories internally except in test-only helpers, if such helpers are explicitly added.

## H. Repository Interface Rules

Repository protocols must follow these rules:

- Return Rebuild-2 schema DTOs or domain DTOs.
- Accept typed IDs from Rebuild-2 schemas where practical.
- Avoid MongoDB ObjectId assumptions.
- Contain no business strategy.
- Contain no product workflow decisions.
- Do not call services.
- Do not call agents.
- Do not call LLM clients.
- Do not call MongoDB in this phase.
- Do not import FastAPI route objects.
- Do not import LangGraph execution code.
- Keep method sets minimal and driven by next-phase needs.

Fake repository implementations must follow these rules:

- Store data in memory only.
- Store deterministic fixture DTOs without requiring ID generation.
- Deep-copy data on save and return to prevent mutation leaks.
- Support reset or clear behavior for tests.
- Reject duplicate IDs consistently.
- Raise `NotFoundError` for missing required records unless a method is explicitly named as optional lookup.
- Keep filtering simple and persistence-like.
- Avoid hidden workflow behavior.

## I. Service Skeleton Rules

Service skeletons must follow these rules:

- Services coordinate repositories.
- Services accept repository dependencies through constructors.
- Services do not call real LLMs.
- Services do not execute LangGraph.
- Services do not implement deep product workflow logic.
- Services do not import FastAPI route objects.
- Services do not import MongoDB clients.
- Services do not import frontend code.
- Services do not construct agent prompts.
- Services may expose simple create, save, get, list, update-status, and read-only composition wrappers.
- Services must remain deterministic and testable with fake repositories.
- Dashboard service may compose a dashboard payload from repositories but must not mutate state or run a workflow.

## J. Fake Repository Behavior Plan

Fake repositories should use in-memory stores keyed by opaque string IDs.

Default behavior:

- `create` or `save_new` stores a new DTO and rejects duplicate IDs.
- `save` may upsert only when explicitly named and justified by the domain.
- `get_by_id` returns a deep copy or raises `NotFoundError`.
- `find_by_id` may return `None` only if a non-raising optional lookup is genuinely useful.
- `list_by_goal_id` filters records by `goal_id`.
- `list_by_run_id` filters records by `run_id`.
- Domain-specific list methods should be added only when used by service tests.
- `update_status` changes only a status field and returns the updated DTO.
- `append_event` is reserved for orchestration run events.
- `clear` or `reset` empties the repository store for tests.

ID behavior:

- Rebuild-2 fixture IDs should be used directly.
- No new ID generation is required in Rebuild-4 unless a tiny deterministic helper is explicitly needed for tests.
- No repository should assume MongoDB ObjectId.

Error behavior:

- Duplicate ID on create raises `DuplicateRecordError`.
- Missing required record raises `NotFoundError`.
- Repository errors should not contain secrets or raw internal traces.

Data isolation behavior:

- Mutating a DTO after saving it must not mutate stored data.
- Mutating a DTO returned by a repository must not mutate stored data.
- Resetting one fake repository instance should not unexpectedly clear another independent instance unless a shared fixture explicitly requests shared state.

## K. Data Ownership Plan

Domain ownership should map as follows:

- `LearningGoalDTO` -> `GoalRepository` -> `GoalService`
- `AssessmentSessionDTO`, `AssessmentAnswerDTO` -> `AssessmentRepository` -> `AssessmentService`
- `KnowledgeMapDTO` -> `KnowledgeMapRepository` -> `KnowledgeMapService`
- `CurriculumDTO` -> `CurriculumRepository` -> `CurriculumService`
- `ResourceDTO`, `ResourceAttachmentDTO` -> `ResourceRepository` -> `ResourceService`
- `ProgressStateDTO` -> `ProgressRepository` -> `ProgressService`
- `QuizDTO`, `QuizAttemptDTO` -> `QuizRepository` -> `QuizService`
- `AdaptationEventDTO` -> `AdaptationRepository` -> `AdaptationService`
- `CriticReviewDTO` -> `CriticReviewRepository` -> `CriticService`
- `EvaluationReportDTO` -> `EvaluationRepository` -> `EvaluationService`
- `OrchestrationRunDTO`, `WorkflowNodeEvent` -> `OrchestrationRunRepository` -> `OrchestrationRunService`
- `DashboardPayload` -> `DashboardService` composed from read-only repository queries

Dashboard ownership rule:

- `DashboardService` may assemble a read model from existing repository data.
- It must not run assessment, knowledge-map, curriculum, RAG, quiz, adaptation, critic, or evaluation logic.

## L. Test Plan For Rebuild-4

Planned tests:

```text
backend\app\tests\test_fake_repositories.py
backend\app\tests\test_repository_data_isolation.py
backend\app\tests\test_service_skeletons.py
backend\app\tests\test_repository_scope_security.py
backend\app\tests\test_dashboard_service_skeleton.py
```

`test_fake_repositories.py` should verify:

- Repository protocol imports.
- Fake repository creation for every domain.
- Create/get/list behavior using Rebuild-2 fixtures.
- Status update behavior where supported.
- Orchestration event append behavior.
- Duplicate handling.
- Not-found behavior.
- Fixtures can be stored and retrieved.

`test_repository_data_isolation.py` should verify:

- Saved DTO mutation after create does not mutate stored data.
- Returned DTO mutation does not mutate stored data.
- Reset or clear empties stores.
- Independent fake repository instances do not leak state.

`test_service_skeletons.py` should verify:

- Service constructors accept protocol-compatible fake repositories.
- Service methods delegate cleanly to repositories.
- Services return schema DTOs.
- No live LLM, network, MongoDB, or LangGraph is needed.

`test_repository_scope_security.py` should verify:

- Repository and service modules do not import MongoDB clients.
- Repository and service modules do not import LLM clients.
- Repository and service modules do not import FastAPI route modules.
- Repository and service modules do not import LangGraph execution modules.
- Repository and service modules do not reference `.env`.

`test_dashboard_service_skeleton.py` should verify, if dashboard service is included:

- Dashboard payload can be composed from fake repository data.
- Composition is read-only.
- Composition does not execute product workflow logic.

## M. Validation Commands

After Rebuild-4 implementation, run from:

```cmd
C:\Users\Fedi\Desktop\PathAI\backend
```

Required commands:

```cmd
python -m compileall app
python -m pytest
python -m ruff check app
python -m mypy app --no-incremental
python -m pytest app\tests\test_live_llm_spike_optional.py -v
```

Expected results:

- Compile passes.
- Default pytest suite passes.
- Ruff passes.
- Mypy passes.
- Optional live LLM tests remain skipped by default.

Do not enable `ENABLE_LIVE_LLM_TESTS`.

## N. File Size And Modularity Rules

Implementation must follow these modularity rules:

- Do not create one giant fake repository file.
- Split fake repositories by domain if the implementation grows.
- Split repository protocols by domain.
- Split services by domain.
- Keep shared fake helper code limited to common in-memory store behavior.
- Avoid circular imports.
- Protocol files should depend on schemas and standard typing only.
- Fake repositories should depend on protocols, errors, fake base helpers, and schemas only.
- Services should depend on repository protocols and schemas only.
- Do not add hidden MongoDB logic.
- Do not add LLM calls.
- Do not add product workflow orchestration.

## O. Security Checklist

Rebuild-4 must satisfy:

- No `.env` access.
- No secrets in fake stores.
- No secrets in tests.
- No MongoDB URI.
- No API keys.
- No tokens.
- No passwords.
- No private credentials.
- No real LLM calls.
- No network calls.
- No frontend exposure.
- No logs with secrets.
- Fake repositories use safe Rebuild-2 fixture data only.
- Errors are sanitized and do not expose private config.

## P. Done Criteria

Rebuild-4 is complete only when:

- Repository protocols exist.
- Repository errors exist.
- Fake repositories exist.
- Service skeletons exist.
- Tests pass.
- Fake repositories can store and retrieve Rebuild-2 fixtures.
- Deep-copy behavior is tested.
- Reset/clear behavior is tested.
- Service skeletons are tested with fake repositories.
- No MongoDB integration is implemented.
- No real LLM call is made.
- No network dependency is introduced.
- No frontend code is changed.
- No auth, Docker, deployment, or CI/CD is implemented.
- No product workflow execution is implemented.
- `reports\phases\rebuild-4\Rebuild_4_Fake_Repositories_And_Service_Skeleton_Result.md` is created.

## Q. Risks And Mitigations

Risk: Fake repositories become business logic.  
Mitigation: Keep fake repositories limited to persistence-like operations: save, get, list, status update, event append, and reset.

Risk: Service skeletons become product workflows.  
Mitigation: Keep services as thin repository boundary wrappers in this phase.

Risk: Too many files create unnecessary friction.  
Mitigation: Use domain files for clarity, but keep methods minimal and avoid speculative helpers.

Risk: One shared fake base becomes a dumping ground.  
Mitigation: Put only copy, storage, duplicate, not-found, and reset helpers in the shared base.

Risk: Circular imports appear between schemas, repositories, and services.  
Mitigation: Keep dependency direction one-way: schemas -> protocols -> fake repositories -> services/tests.

Risk: Mutation leaks corrupt fake repository state.  
Mitigation: Deep-copy on save and return, and add explicit data-isolation tests.

Risk: Fake repository interfaces do not match future Mongo repositories.  
Mitigation: Define repository protocols around persistence use cases, not fake-specific details.

Risk: Overbuilding methods too early.  
Mitigation: Add only methods exercised by Rebuild-2 fixtures, service skeletons, and near-term tests.

Risk: Underbuilding methods needed by Rebuild-5 or Rebuild-6.  
Mitigation: Include basic create/get/list/update/event operations for all major artifacts.

Risk: Dashboard service is introduced too early.  
Mitigation: If included, keep it read-only and composed from already stored DTOs.

## R. Required Rebuild-4 Result Recap Structure

Implementation must create:

```text
C:\Users\Fedi\Desktop\PathAI\reports\phases\rebuild-4\Rebuild_4_Fake_Repositories_And_Service_Skeleton_Result.md
```

The result recap must include:

```text
A. Scope
B. MAIN.md / RULES.md Compliance
C. Files Created or Updated
D. Work Completed
E. Validation Commands And Results
F. Security / Secret Handling
G. Repository / Service Skeleton Result
H. Not Done / Intentionally Postponed
I. Remaining Risks
J. Next Recommended Phase
```

The recap must honestly report exact validation results and any warnings.

## S. Recommended Implementation Sequence

1. Re-read `docs\architecture\MAIN.md` and `docs\architecture\RULES.md`.
2. Re-read `reports\phases\Phase_Roadmap_Alignment_Note.md`.
3. Inspect Rebuild-2 schemas and fixtures.
4. Confirm repository and service packages are still skeleton-only.
5. Implement repository errors.
6. Implement repository protocols by domain.
7. Implement shared fake repository base/helper if useful.
8. Implement fake repositories by domain.
9. Implement service skeletons by domain.
10. Add repository, service, dashboard, isolation, and scope/security tests.
11. Run validation commands.
12. Fix only Rebuild-4-scoped issues.
13. Create the Rebuild-4 result recap.

## T. Final Recommendation

Rebuild-4 implementation should begin after this action plan is approved.

The implementation should stay limited to repository protocols, fake repositories, service skeletons, deterministic tests, and the Rebuild-4 result recap. It must not introduce MongoDB, real LLM calls, LangGraph execution, product API routes, frontend code, authentication, Docker, deployment, or full product workflow behavior.
