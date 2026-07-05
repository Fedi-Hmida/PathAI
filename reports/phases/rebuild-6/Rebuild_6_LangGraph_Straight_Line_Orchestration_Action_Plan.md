# Rebuild-6 LangGraph Straight-Line Orchestration Action Plan

Status: Action plan  
Project: PathAI  
Phase: Rebuild-6  
Created: 2026-07-05  

## A. Phase Objective

Rebuild-6 should introduce the first PathAI orchestration layer using LangGraph, lightweight workflow state, fake-backed services, and deterministic fixture/mock behavior.

The objective is not to build the full AI workflow. The objective is to prove that PathAI can represent and execute a clean orchestration shape without violating the architecture:

- LangGraph coordinates node order and state transitions.
- Services remain the boundary for persistence decisions.
- Repositories remain the persistence abstraction.
- Full artifacts stay in repositories, not graph state.
- The run remains deterministic and testable without network, MongoDB, or live LLM calls.

This phase matters because PathAI now has schemas, fixtures, fake repositories, service skeletons, and a fake-backed API boundary, but no orchestration execution layer. Rebuild-6 should add the first straight-line orchestration skeleton so later phases can safely replace deterministic fixture behavior with real agents and richer branching.

## B. MAIN.md / RULES.md Alignment

This phase is governed by:

- `docs\architecture\MAIN.md`
- `docs\architecture\RULES.md`
- `reports\phases\Phase_Roadmap_Alignment_Note.md`
- `reports\phases\rebuild-2\Rebuild_2_Core_Schemas_Contracts_And_Mock_LLM_Fixtures_Result.md`
- `reports\phases\rebuild-4\Rebuild_4_Fake_Repositories_And_Service_Skeleton_Result.md`
- `reports\phases\rebuild-5\Rebuild_5_Backend_Product_API_Boundary_With_Fake_Services_Result.md`

Relevant governing rules:

- LangGraph coordinates workflow state and node execution, not database storage.
- `WorkflowState` must stay lightweight.
- Full artifacts live in repositories, not graph state.
- Graph nodes must not bypass services for persistence.
- Services own orchestration entry points and persistence decisions.
- Repositories own persistence abstraction.
- Agents must remain persistence-free.
- Agents are not implemented in this phase.
- No real LLM calls are allowed by default.
- Default orchestration tests must be independent of live LLM calls.
- No MongoDB integration is allowed in this phase.
- Deterministic tests come before live LLM behavior.
- Mock/deterministic behavior must allow the demo path to run without network access.
- Files must be small, focused, and separated by responsibility.
- `.env` must not be read, printed, copied, modified, or exposed.
- Future-phase behavior must not be implemented early.

## C. Current Starting Point

Current state after Rebuild-5:

- Backend foundation is green.
- FastAPI app, settings, logging, health, and readiness exist.
- Rebuild-2 schemas and contracts are complete.
- Deterministic canonical fixtures and mock agent fixtures are complete.
- Fake repositories are complete.
- Service skeletons are complete.
- Fake-backed API product boundary is complete.
- API validation was green in Rebuild-5:
  - compile passed
  - pytest passed with `53 passed, 3 skipped`
  - Ruff passed
  - mypy passed
  - optional live LLM tests stayed skipped
- `backend\app\orchestration` currently contains only `__init__.py`.
- `backend\pyproject.toml` does not currently declare `langgraph`.
- No LangGraph execution exists yet.
- No real LLM has been used.
- No MongoDB has been used.

## D. In Scope

Allowed Rebuild-6 work:

- LangGraph dependency check.
- Minimal LangGraph dependency declaration if needed and approved during implementation.
- Small orchestration package structure.
- Lightweight workflow state helper/adapter if needed.
- Straight-line graph builder.
- Deterministic graph node functions.
- Orchestration runner/service skeleton.
- Node event creation and recording.
- Orchestration status progression.
- Integration with fake-backed services.
- Tests for graph import/build behavior.
- Tests for deterministic straight-line execution.
- Tests proving state remains lightweight.
- Tests proving node events/statuses are recorded.
- Controlled failure-path test if feasible.
- Scope/security tests for forbidden imports/calls.
- Rebuild-6 result recap.

Optional and only if justified during implementation:

- A small internal/demo API endpoint to trigger the fake graph, if a later implementation decision explicitly needs it.

Recommended default:

- Do not add a public orchestration execution endpoint in Rebuild-6.
- Test the runner directly.
- Leave existing Rebuild-5 read/status endpoints unchanged.

## E. Out Of Scope

Explicitly excluded:

- Real LLM calls.
- Live LLM tests.
- Real agent implementation.
- Product prompt engineering.
- Prompt templates for real agents.
- MongoDB repositories.
- Beanie, Motor, PyMongo, or database connections.
- Production persistence.
- RAG ranking.
- Quiz scoring algorithm.
- Adaptation execution logic.
- Critic revision loops.
- Assessment loops.
- Complex conditional branching.
- Real orchestration workflow complexity.
- Frontend code.
- Authentication.
- JWT/login/register.
- Password hashing.
- Sessions or protected routes.
- Docker.
- Deployment.
- CI/CD.
- Production background jobs.
- `.env` access.

## F. Dependency Strategy

Current dependency state:

- `backend\pyproject.toml` does not currently declare `langgraph`.
- Rebuild-6 is the first phase that may need the LangGraph runtime.

Implementation plan:

- During implementation, first check whether `langgraph` is already importable in the backend virtual environment.
- If not declared/importable, add only the minimal `langgraph` dependency to `backend\pyproject.toml`.
- Do not add unrelated AI libraries.
- Do not add LangChain provider packages unless a future phase explicitly requires them.
- Do not add live LLM provider dependencies.
- Keep default tests deterministic.
- Do not require network calls at runtime.
- If dependency installation is needed, use the backend virtual environment and record the exact command/result in the implementation recap.
- If dependency installation fails because of network/sandbox restrictions, report the exact error and do not fake success.

Recommended dependency target:

```text
langgraph
```

The exact version constraint should be conservative and compatible with Python 3.11+ and current FastAPI/Pydantic dependencies. Prefer a stable lower bound rather than an overly narrow pin unless implementation proves a pin is necessary.

## G. Proposed Orchestration Structure

Create small modules under:

```text
backend\app\orchestration
```

Recommended files:

- `backend\app\orchestration\__init__.py`
  - Public orchestration exports only.
  - No side-effectful graph execution at import time.

- `backend\app\orchestration\state.py`
  - Lightweight state construction helpers.
  - State merge/update helpers if LangGraph requires dict-shaped state.
  - Conversion helpers between runtime state shape and `WorkflowState` if needed.
  - No full DTO artifact storage.

- `backend\app\orchestration\nodes.py`
  - Deterministic straight-line node functions.
  - Each node accepts state and an injected context/service bundle.
  - Nodes call services, not repositories directly.
  - Nodes store only IDs/status metadata in state.

- `backend\app\orchestration\graph.py`
  - LangGraph builder.
  - Node registration.
  - Straight-line edge definition.
  - Compile/build helper.
  - No hidden global fake service container.

- `backend\app\orchestration\runner.py`
  - Orchestration runner class/function.
  - Accepts fake-backed services or a service bundle.
  - Initializes state.
  - Runs the graph.
  - Returns final `WorkflowState` or a small runner result.

- `backend\app\orchestration\events.py`
  - Helpers for `WorkflowNodeEvent`.
  - Node started/completed/failed event construction.
  - Safe warning/error conversion.

- `backend\app\orchestration\errors.py`
  - Orchestration-specific exceptions.
  - Sanitized error categories/messages for state/events.

Rules:

- No giant graph file.
- No services or repositories hidden inside module globals.
- No circular imports.
- No API route imports inside orchestration modules.
- No MongoDB imports.
- No LLM client imports.
- No agent imports in Rebuild-6.

## H. Lightweight WorkflowState Plan

Use the existing Rebuild-2 `WorkflowState` schema as the canonical workflow-state contract.

The graph state may contain:

- `run_id`
- `goal_id`
- `assessment_session_id`
- `knowledge_map_id`
- `curriculum_id`
- `progress_state_id`
- `quiz_id`
- `quiz_attempt_id`
- `adaptation_event_ids`
- `critic_review_id`
- `evaluation_report_id`
- `current_node`
- `status`
- `mode`
- `pending_user_action`
- `assessment_question_count`
- `assessment_confidence`
- `critic_revision_attempts`
- `repeated_stuck_count`
- `quiz_score`
- `errors`
- `warnings`
- `node_attempts`
- `created_at`
- `updated_at`
- `completed_at`
- `trace_metadata`

If implementation needs additional runtime-only metadata, keep it minimal and explicitly named. Do not persist or expose runtime-only helper objects as canonical workflow state.

Rules:

- Do not store full `LearningGoalDTO` in state.
- Do not store full `AssessmentSessionDTO` in state.
- Do not store full `KnowledgeMapDTO` in state.
- Do not store full `CurriculumDTO` in state.
- Do not store resource lists in state.
- Do not store full `QuizDTO` or quiz answers in state.
- Do not store `DashboardPayload` in state.
- Do not store full persisted artifacts or nested documents in state.
- Fetch and store full artifacts through services.
- Store only IDs, statuses, counters, warnings, errors, summaries, and trace metadata.

## I. Straight-Line Graph Node Plan

Rebuild-6 should implement a straight-line deterministic graph only.

Recommended node order:

1. `initialize_run`
2. `load_goal`
3. `load_assessment`
4. `load_knowledge_map`
5. `load_curriculum`
6. `load_resources`
7. `load_critic_review`
8. `load_progress`
9. `load_quiz`
10. `load_adaptation`
11. `load_evaluation`
12. `prepare_dashboard_payload`
13. `complete_run`

Node responsibilities:

- `initialize_run`
  - Create or confirm an `OrchestrationRunDTO`.
  - Set state status to running.
  - Record the initial run ID and goal ID.

- `load_goal`
  - Store or fetch the canonical goal through `GoalService`.
  - Record `goal_id`.

- `load_assessment`
  - Store or fetch canonical assessment session and answers through `AssessmentService`.
  - Record `assessment_session_id`, question count, and confidence.

- `load_knowledge_map`
  - Store or fetch canonical knowledge map through `KnowledgeMapService`.
  - Record `knowledge_map_id`.

- `load_curriculum`
  - Store or fetch canonical curriculum through `CurriculumService`.
  - Record `curriculum_id`.

- `load_resources`
  - Store or fetch canonical resources and attachments through `ResourceService`.
  - Do not perform ranking.
  - Do not store resource lists in state.

- `load_critic_review`
  - Store or fetch canonical critic review through `CriticService`.
  - Record `critic_review_id`.

- `load_progress`
  - Store or fetch canonical progress state through `ProgressService`.
  - Record `progress_state_id`.

- `load_quiz`
  - Store or fetch canonical quiz and quiz attempt through `QuizService`.
  - Record `quiz_id`, `quiz_attempt_id`, and lightweight `quiz_score`.
  - Do not score quiz answers.

- `load_adaptation`
  - Store or fetch canonical adaptation event through `AdaptationService`.
  - Record `adaptation_event_ids`.
  - Do not execute adaptation.

- `load_evaluation`
  - Store or fetch canonical evaluation report through `EvaluationService`.
  - Record `evaluation_report_id`.
  - Do not compute evaluation formulas.

- `prepare_dashboard_payload`
  - Call `DashboardService.get_by_run_id`.
  - Confirm dashboard can be composed.
  - Do not store dashboard payload in state.

- `complete_run`
  - Mark state completed.
  - Mark `OrchestrationRunDTO` completed.
  - Record final completed timestamp.

Rules for all nodes:

- Use fake-backed services and deterministic fixtures.
- Save/read artifacts through services.
- Update only lightweight state fields.
- Record node events.
- Do not call LLM.
- Do not call MongoDB.
- Do not import or execute agents.
- Do not execute real business intelligence.
- Do not implement loops or branching in this phase.

## J. Node Event And Status Plan

Node event behavior:

- Each node should record a completed event on success.
- A failure path should record a failed event with sanitized error metadata.
- A started event is optional. If implemented, tests must expect the exact event count/order.
- Skipped events are optional and should only be used if a node is deliberately no-op because an artifact already exists.

Event fields should use `WorkflowNodeEvent`:

- `run_id`
- `node_name`
- `status`
- `attempt_count`
- `message`
- `created_at`
- `errors`
- `warnings`

Status behavior:

- Initial state: queued or running, depending on runner entrypoint.
- While executing: running.
- On successful completion: completed.
- On controlled failure: failed.

Persistence/event rules:

- Append node events through `OrchestrationRunService.append_event`.
- Update run status through `OrchestrationRunService.update_status` or `save`.
- Keep event messages short and safe.
- Do not store raw stack traces in events.
- Do not store secrets or config values in events.
- Do not pretend success if a node fails.

## K. Runner / Service Plan

Create an orchestration runner that:

- Accepts a fake-backed service bundle or existing Rebuild-5 `ApiServiceContainer`.
- Accepts initial `run_id` and `goal_id`, or creates a deterministic demo run from canonical IDs.
- Creates an initial lightweight `WorkflowState`.
- Executes the straight-line graph.
- Returns final `WorkflowState`.
- Optionally returns the final `OrchestrationRunDTO` as part of a small runner result.
- Does not own persistence directly.
- Does not instantiate repositories directly outside explicit container/test setup.
- Does not instantiate MongoDB.
- Does not call LLM.
- Does not call agents.

Relationship to `OrchestrationRunService`:

- The runner uses `OrchestrationRunService` to create/update the run summary and append node events.
- The runner does not replace `OrchestrationRunService`.
- `OrchestrationRunService` remains the service boundary for run persistence operations.

Recommended service bundle:

- Use a small dataclass-like orchestration context that references the services needed by nodes.
- The context may be built from Rebuild-5 `ApiServiceContainer` in tests.
- Keep context construction outside node functions.

## L. API Boundary Decision

Recommended Rebuild-6 decision:

- Do not add a public orchestration execution endpoint in this phase.
- Test the runner directly.
- Keep Rebuild-5 read/status endpoints unchanged.

Reasoning:

- Rebuild-5 already exposes read/status API boundaries.
- Rebuild-6 should focus on graph correctness and architecture boundaries.
- Adding a public execution endpoint too early could create API contract churn.
- Frontend integration is postponed.

If implementation later adds a demo-only internal execution endpoint, it must:

- remain fake-backed
- be explicitly labeled deterministic demo behavior
- call a service/runner, not graph internals from a route
- avoid real LLM, MongoDB, network, and agents
- include tests proving it does not execute future-phase logic

## M. Test Plan For Rebuild-6

Add focused tests under:

```text
backend\app\tests
```

Suggested test files:

- `test_orchestration_state.py`
  - validates initial workflow state construction
  - confirms state contains IDs/status/counters only
  - confirms no full DTOs are embedded

- `test_orchestration_graph_build.py`
  - imports graph modules
  - builds/compiles the graph
  - confirms expected node names and straight-line order where feasible

- `test_orchestration_straight_line.py`
  - executes the deterministic graph with fake-backed services
  - confirms final status is completed
  - confirms IDs are preserved
  - confirms canonical artifacts are available through services after execution

- `test_orchestration_events.py`
  - confirms node events are appended
  - confirms event order matches straight-line node order
  - confirms completed/failed nodes are recorded correctly

- `test_orchestration_scope_security.py`
  - scans orchestration modules for forbidden imports/references
  - rejects `.env` references
  - rejects MongoDB, Beanie, Motor, PyMongo
  - rejects LLM clients and real provider imports
  - rejects agents
  - rejects frontend imports
  - rejects network clients

Required test scenarios:

- Graph imports cleanly.
- Graph builds successfully.
- Straight-line graph executes with fake services.
- Completed nodes are recorded in order.
- Node events are recorded.
- Orchestration status becomes completed.
- IDs are preserved.
- State remains lightweight.
- Full DTOs are not embedded in state.
- One controlled fake failure marks failed status if feasible.
- No real LLM, network, MongoDB, agents, frontend, auth, Docker, deployment, or `.env` is required.

## N. Validation Commands

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

## O. File Size And Modularity Rules

Implementation must follow:

- No giant orchestration file.
- Split state, nodes, graph, runner, events, and errors.
- Graph nodes should be short and deterministic.
- Avoid hidden global service containers.
- Avoid circular imports.
- Do not duplicate schemas.
- Do not bypass the service layer.
- Do not import API routes into orchestration modules.
- Do not put real agent/LLM code in graph nodes.
- Do not use orchestration modules as a dumping ground for future business logic.

## P. Security Checklist

Before Rebuild-6 is complete, confirm:

- No `.env` access.
- No `.env` content read, printed, copied, modified, or exposed.
- No secrets in state.
- No secrets in node events.
- No secrets in logs.
- No API keys.
- No tokens.
- No passwords.
- No MongoDB URI.
- No private credentials.
- No LLM calls.
- No network calls.
- No MongoDB calls.
- No raw internal errors or stack traces persisted in event DTOs.
- No credentials in tests or fixtures.
- Optional live LLM tests remain skipped by default.

## Q. Done Criteria

Rebuild-6 is complete only when:

- LangGraph dependency is declared/available if needed.
- Orchestration modules exist.
- Lightweight state adapter/helper exists if needed.
- Straight-line graph builds.
- Straight-line graph executes deterministically.
- Node events are recorded.
- Run status progresses and completes.
- State remains lightweight and ID-based.
- Tests pass.
- Ruff passes.
- mypy passes.
- Optional live LLM tests remain skipped by default.
- No real LLM, MongoDB, network, frontend, auth, Docker, deployment, agents, RAG ranking, quiz scoring, adaptation execution, or evaluation formula implementation is added.
- Rebuild-6 result recap is created.

## R. Risks And Mitigations

Risks:

- Graph state bloat.
- Nodes bypass services and write directly to repositories.
- Deterministic fake workflow is mistaken for real AI workflow.
- LangGraph dependency/version issues.
- Graph becomes too complex too early.
- Hidden global state makes tests flaky.
- Event recording becomes inconsistent.
- Runner becomes a business-service dumping ground.
- Tests become brittle around exact node internals.
- Future real agent integration mismatches the deterministic node contract.

Mitigations:

- Keep state ID-only and test for absence of full DTOs.
- Require nodes to use services.
- Label deterministic behavior clearly in docs/tests.
- Add only minimal LangGraph dependency.
- Use straight-line graph only.
- Inject service bundle/context explicitly.
- Centralize event helpers.
- Keep runner focused on graph execution.
- Test observable outcomes rather than private implementation details where possible.
- Keep node inputs/outputs aligned with existing schema contracts.

## S. Required Rebuild-6 Result Recap Structure

Implementation must create:

```text
C:\Users\Fedi\Desktop\PathAI\reports\phases\rebuild-6\Rebuild_6_LangGraph_Straight_Line_Orchestration_Result.md
```

It must include:

```text
A. Scope
B. MAIN.md / RULES.md Compliance
C. Files Created or Updated
D. Work Completed
E. Validation Commands And Results
F. Security / Secret Handling
G. LangGraph / Orchestration Result
H. Not Done / Intentionally Postponed
I. Remaining Risks
J. Next Recommended Phase
```

The recap must honestly record dependency changes, installation results if any, validation results, warnings, and anything intentionally postponed.

## T. Recommended Implementation Sequence

1. Re-read `MAIN.md` and `RULES.md`.
2. Inspect existing orchestration folder, schemas, services, fake repositories, API container, and fixtures.
3. Check whether `langgraph` is declared and importable.
4. Add minimal dependency only if needed.
5. Design lightweight state helpers.
6. Implement orchestration errors and event helpers.
7. Implement deterministic straight-line nodes.
8. Implement graph builder.
9. Implement runner with injected fake-backed services/context.
10. Add orchestration tests.
11. Add scope/security tests.
12. Run validation.
13. Fix only Rebuild-6 scoped issues.
14. Create the Rebuild-6 result recap.

## U. Final Recommendation

Rebuild-6 implementation should begin after this action plan is approved.

The implementation must remain a straight-line orchestration skeleton phase only. It should prove LangGraph shape, lightweight state, service-bound node behavior, node event recording, and deterministic execution with fake-backed services. It must not implement real agents, real LLM calls, MongoDB, RAG ranking, quiz scoring, adaptation execution, evaluation formulas, frontend, auth, Docker, deployment, or production background jobs.
