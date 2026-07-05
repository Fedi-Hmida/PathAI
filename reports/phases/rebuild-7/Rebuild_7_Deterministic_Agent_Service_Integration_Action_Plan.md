# Rebuild-7 Action Plan: Deterministic Agent Service Integration Behind The Orchestration Boundary

## Planning Task Status

The required references were checked: `MAIN.md`, `RULES.md`, and the Rebuild-6 result exist and were reviewed.

Existing backend inspection shows:

- `backend/app/agents` is currently empty except `__init__.py`.
- Rebuild-2 agent schemas already exist.
- Deterministic mock agent outputs already exist in fixtures.
- Rebuild-6 orchestration currently loads canonical artifacts directly through services.

This plan is documentation-only. It does not implement backend runtime code.

## A. Phase Objective

Rebuild-7 should move PathAI from a straight-line graph that loads prebuilt deterministic artifacts into a straight-line graph that calls deterministic, agent-shaped service boundaries.

The phase exists after Rebuild-6 because Rebuild-6 proved the orchestration shape, state handling, node ordering, and event recording. Rebuild-7 should now prove the next architecture layer: agents as typed transformation components, wrapped by services, with deterministic mock implementations that future live LLM agents can replace safely.

This is not a real AI-agent phase. It is a contract, mock, service-boundary, and orchestration-integration phase.

## B. MAIN.md / RULES.md Alignment

This phase follows the canonical rules:

- `MAIN.md` says agents receive structured inputs and return structured outputs.
- Services decide when agents run, validate outputs, and decide what is persisted.
- Agents must not write to repositories, know collection names, or own persistence.
- API routes must not call agents directly.
- Repositories must not call agents or LLMs.
- LangGraph coordinates workflow execution, not storage.
- `WorkflowState` must stay lightweight: IDs, statuses, counters, warnings, errors, trace metadata, and timestamps only.
- Full artifacts remain in repositories/services.
- Deterministic mock behavior comes before live LLM behavior.
- Default tests must not require network, MongoDB, or real LLM calls.
- `.env` must not be read, printed, copied, modified, or exposed.

Roadmap alignment note:

`MAIN.md` contains older roadmap labels where Rebuild-6 and Rebuild-7 refer to deeper product phases such as assessment/knowledge-map and curriculum/resources/critic. The current implemented phase history has already documented roadmap alignment and completed Rebuild-6 as straight-line LangGraph orchestration. Therefore this Rebuild-7 is an intermediate safety phase: deterministic agent-service integration behind the orchestration boundary before real product intelligence.

## C. Current Starting Point

Current system state after Rebuild-6:

- Rebuild-2 schemas/contracts exist, including agent input/output DTOs.
- Deterministic canonical fixtures and mock agent output fixtures exist.
- Rebuild-4 fake repositories and service skeletons exist.
- Rebuild-5 fake-backed API boundary exists.
- Rebuild-6 straight-line LangGraph orchestration exists.
- The graph currently loads canonical artifacts directly through services.
- `backend/app/agents` currently has no real agent modules.
- No real LLM, no MongoDB, no full AI workflow, and no real agent behavior exists yet.

## D. In Scope

Allowed Rebuild-7 work:

- Agent protocol/interface definitions.
- Deterministic mock agent implementations.
- Agent service boundary classes that call agents and validate outputs.
- Wiring an explicit agent service bundle into orchestration context.
- Updating deterministic graph nodes to call agent services instead of directly loading all prebuilt outputs.
- Persisting schema-valid deterministic outputs through existing domain services.
- Safe event/status recording with agent names and artifact IDs.
- Failure handling for malformed mock output or controlled agent failure.
- Tests for contracts, mocks, services, orchestration integration, lightweight state, and forbidden imports.
- Result recap creation.

## E. Out Of Scope

Explicitly excluded:

- Real LLM calls.
- Live LLM tests.
- Production prompt templates.
- Provider-specific LLM adapters.
- MongoDB repositories.
- Production persistence.
- Frontend work.
- Authentication, JWT, login/register, password hashing, sessions, or protected routes.
- Docker.
- Deployment.
- CI/CD.
- Real RAG ranking.
- Real quiz scoring algorithms.
- Real adaptation execution logic.
- Critic revision loops.
- Assessment loops.
- Background jobs.

## F. Proposed File Structure

Use the existing empty `backend/app/agents` package and keep files small:

- `backend/app/agents/__init__.py`
- `backend/app/agents/errors.py`
- `backend/app/agents/contracts.py`
- `backend/app/agents/mock/__init__.py`
- `backend/app/agents/mock/assessment.py`
- `backend/app/agents/mock/knowledge_map.py`
- `backend/app/agents/mock/curriculum.py`
- `backend/app/agents/mock/resource.py`
- `backend/app/agents/mock/critic.py`
- `backend/app/agents/mock/progress.py`
- `backend/app/agents/mock/quiz.py`
- `backend/app/agents/mock/adaptation.py`
- `backend/app/agents/mock/evaluation.py`
- `backend/app/agents/services/__init__.py`
- `backend/app/agents/services/bundle.py`
- `backend/app/agents/services/assessment.py`
- `backend/app/agents/services/knowledge_map.py`
- `backend/app/agents/services/curriculum.py`
- `backend/app/agents/services/resource.py`
- `backend/app/agents/services/critic.py`
- `backend/app/agents/services/progress.py`
- `backend/app/agents/services/quiz.py`
- `backend/app/agents/services/adaptation.py`
- `backend/app/agents/services/evaluation.py`

Update orchestration only where needed:

- `backend/app/orchestration/nodes.py`
- `backend/app/orchestration/runner.py`
- `backend/app/orchestration/events.py` if agent metadata is needed
- `backend/app/orchestration/__init__.py`

Do not create one giant agent file, one giant mock file, or one mega-service.

## G. Agent Contract Strategy

Use existing Rebuild-2 schema DTOs wherever possible.

Define protocols in `backend/app/agents/contracts.py`:

- `AssessorAgent`: accepts `AssessmentAgentInput`, returns `AssessmentAgentOutput`; optional scoring method accepts answer context and returns `AssessmentScoreOutput`.
- `KnowledgeMapAgent`: accepts `KnowledgeMapAgentInput`, returns `KnowledgeMapAgentOutput`.
- `CurriculumAgent`: accepts `CurriculumAgentInput`, returns `CurriculumAgentOutput`.
- `ResourceAgent`: accepts `ResourceAgentInput`, returns `ResourceAgentOutput`.
- `CriticAgent`: accepts `CriticAgentInput`, returns `CriticAgentOutput`.
- `ProgressAgent`: use existing progress DTOs and canonical deterministic progress construction; if no dedicated schema exists, keep the contract service-level and do not invent broad new schemas.
- `QuizAgent`: accepts `QuizAgentInput`, returns `QuizAgentOutput`; optional scoring method returns `QuizScoreOutput`.
- `AdapterAgent`: accepts `AdaptationAgentInput`, returns `AdaptationAgentOutput`.
- `EvaluationAgent`: accepts `EvaluationAgentInput`, returns `EvaluationAgentOutput`.

Contracts must not mention LLM providers, prompts, MongoDB, HTTP routes, or frontend types.

## H. Deterministic Mock Agent Strategy

Mock agents should:

- Return existing schema-valid outputs from `backend/app/fixtures/mock_agents.py`.
- Use canonical demo fixtures as the deterministic source.
- Avoid network, real LLM calls, randomness, current clock drift, and environment reads.
- Return deep copies or freshly validated models so callers cannot mutate shared fixtures.
- Support one controlled malformed/failing behavior for tests through explicit constructor flags, not randomness.
- Never log or expose raw prompt-like content.
- Be useful for local demo and tests while remaining obviously non-production.

## I. Agent Service Boundary Strategy

Agent services should wrap agent behavior and be the only layer that calls agent protocols.

Rules:

- API routes do not call agents.
- Repositories do not call agents.
- Graph nodes call agent services or an explicit `AgentServiceBundle`.
- Agent services validate agent outputs with Pydantic before converting/saving artifacts.
- Agent services persist through existing domain services only.
- Agent services do not know fake repository internals.
- Agent services do not expose provider-specific LLM details.
- Services should return persisted DTOs and/or created artifact IDs, not raw agent outputs unless the test explicitly targets the contract.

## J. Orchestration Integration Strategy

Evolve Rebuild-6 nodes as follows:

- Keep the same straight-line graph and node names unless a tiny rename is needed for clarity.
- Replace direct canonical artifact loading in agent-owned nodes with deterministic agent service calls.
- Keep `initialize_run`, `prepare_dashboard_payload`, and `complete_run` as orchestration/service operations.
- Agent-backed nodes should create typed inputs from existing persisted artifacts, call the relevant agent service, persist resulting DTOs through domain services, and update state with artifact IDs only.
- Resource, progress, quiz, adaptation, critic, and evaluation nodes remain deterministic and schema-valid.
- No branching, loops, retries, real scoring, real RAG ranking, or real adaptation execution in this phase.

## K. Lightweight State Protection

Implementation must forbid storing these in `WorkflowState` or LangGraph state:

- Full DTOs.
- Dashboard payloads.
- Raw agent outputs.
- Raw LLM outputs.
- Prompt contents.
- Large resource lists.
- Full curriculum objects.
- Full quiz objects.
- Full knowledge maps.
- Full assessment sessions or answers.
- Secret-bearing config.
- Provider names, model names, credentials, or API details.

Allowed state values:

- IDs.
- Node name.
- Status.
- Counters.
- Warning/error summaries.
- Safe artifact ID mappings.
- Timestamps.
- Trace metadata.

## L. Event And Error Strategy

Agent-related node events should include:

- `run_id`
- node name
- agent name
- status
- timestamp
- safe message
- created artifact ID when applicable
- warning/error category when applicable

Events must not include:

- stack traces
- secrets
- raw model output
- full DTOs
- prompts
- provider errors
- credentials
- `.env` values

Failures should use sanitized `AgentError` / `AgentOutputValidationError` types and be recorded as controlled workflow failures.

## M. Testing Strategy

Add focused tests:

- `test_agent_contracts.py`: protocols and mock agent implementations import cleanly and satisfy expected methods.
- `test_mock_agents.py`: deterministic mocks return schema-valid outputs and stable data.
- `test_agent_services.py`: services call mock agents, validate output, and persist via domain services.
- `test_orchestration_agent_integration.py`: graph executes through agent services and records artifact IDs.
- `test_agent_events.py`: node events include safe agent metadata and no raw outputs.
- `test_agent_failure_handling.py`: controlled malformed/failing mock output marks workflow failed safely.
- `test_agent_scope_security.py`: agents/services/orchestration do not import MongoDB, FastAPI routes, frontend code, LLM clients, network clients, Docker, auth, or `.env`.

Existing API, repository, schema, and orchestration tests must remain green.

## N. Validation Commands

Future implementation must run from:

`C:\Users\Fedi\Desktop\PathAI\backend`

Commands:

```cmd
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check app
.\.venv\Scripts\python.exe -m mypy app --no-incremental
.\.venv\Scripts\python.exe -m pytest app\tests\test_live_llm_spike_optional.py -v
```

Live LLM tests must remain skipped by default.

## O. Security Checklist

Implementation must confirm:

- Do not read `.env`.
- Do not print secrets.
- Do not call a real LLM.
- Do not access network.
- Do not add credentials to fixtures.
- Do not add API keys in tests/docs.
- Do not use MongoDB URIs.
- Do not log raw prompts.
- Do not log raw model outputs.
- Do not expose provider errors.
- Do not store secret-bearing config in state/events.

## P. Best-Practice Rules For Implementation

- Keep files small.
- No mega-service.
- No mega-agent file.
- No route business logic.
- No repository business logic.
- No orchestration state bloat.
- No duplicated schemas.
- No hidden global mutable state except controlled fake test stores already established.
- No future-phase work.
- No provider-specific assumptions.
- No direct route-to-agent or repository-to-agent coupling.
- No prompt templates unless explicitly scoped later.
- Validate every agent output before persistence.

## Q. Risks

Main risks:

- Accidentally building real agent logic too early.
- Turning deterministic mocks into hidden business logic.
- Storing full artifacts or raw outputs in graph state.
- Coupling routes directly to agents.
- Coupling repositories directly to agents.
- Creating fragile mocks that only test the happy path.
- Making future real LLM replacement hard by leaking mock assumptions into services.
- Introducing oversized agent/service files.
- Duplicating schemas already defined in Rebuild-2.
- Recording unsafe event/error details.

## R. Done Criteria

Rebuild-7 implementation is complete only when:

- Agent protocols exist for all required agent roles.
- Deterministic mock agents exist and return schema-valid outputs.
- Agent services wrap mock agents and persist through existing domain services.
- Orchestration nodes call agent services instead of directly loading all deterministic artifacts.
- Workflow state remains lightweight.
- Node events record safe agent metadata.
- Controlled agent failure is tested.
- Scope/security tests prove no forbidden imports or `.env` references.
- Compile, pytest, Ruff, mypy, and live-LLM skip confirmation pass.
- Result recap is created.
- No real LLM, MongoDB, frontend, auth, Docker, deployment, CI/CD, or future-phase work is implemented.

## S. Result Recap Requirements

Future implementation must create:

`reports/phases/rebuild-7/Rebuild_7_Deterministic_Agent_Service_Integration_Result.md`

The recap must include:

A. Rebuild-7 Result  
B. MAIN.md / RULES.md Compliance  
C. Agent Contracts Added  
D. Deterministic Mock Agents Added  
E. Agent Services Added  
F. Orchestration Integration  
G. Validation Results  
H. Security / Secret Handling  
I. Not Done  
J. Next Step

## T. Implementation Sequence

1. Re-read `MAIN.md`, `RULES.md`, and Rebuild-6 result.
2. Inspect existing schemas, fixtures, services, and orchestration nodes.
3. Create agent errors and protocols.
4. Create deterministic mock agent modules backed by existing mock fixture outputs.
5. Create agent service modules that validate outputs and persist through existing domain services.
6. Create an `AgentServiceBundle` for orchestration injection.
7. Extend orchestration context/runner to accept the agent service bundle.
8. Update nodes one at a time to call agent services while preserving straight-line graph order.
9. Add tests for contracts, mocks, services, orchestration integration, events, failure handling, lightweight state, and forbidden imports.
10. Run full validation.
11. Fix only Rebuild-7 scoped issues.
12. Create the Rebuild-7 result recap.

## U. Final Recommendation

Rebuild-7 implementation should begin after this plan is reviewed and the session is allowed to perform file mutations for runtime work. The implementation should remain deterministic, mock-first, service-wrapped, and orchestration-safe.
