# PathAI MAIN Blueprint

> This is the latest canonical MAIN file for the PathAI rebuild.
>
> The original files are preserved as historical/source material.
>
> Future implementation phases should use this MAIN file as the primary reference.
>
> `RULES.md` is the mandatory execution rulebook for all future phases and must be read together with this MAIN blueprint.
>
> **Rebuild-25 addendum:** gate-only JWT authentication (users,
> register/login/refresh/logout, behind `PATHAI_ENABLE_AUTH`, default off)
> was implemented as an explicitly-approved exception to this document's
> no-auth target — see `docs/decisions/0001-jwt-authentication-gate-only.md`
> and `RULES.md` §7/§15. The no-auth demo journey described below is
> unaffected when the flag is off (the default); per-user data ownership is
> not part of this exception and remains a future phase.

## Merged Sources

This MAIN file preserves the full latest content from these source documents:

1. `docs\architecture\Rebuild_0B_Architecture_Contracts_And_Roadmap.md`
2. `reports\phases\Rebuild_0B_Correction_Pass_Result.md`
3. `reports\phases\Rebuild_0B_Architecture_Contracts_And_Roadmap_Result.md`

---

## Source 1: Rebuild-0B Architecture, Contracts, And Roadmap

> Canonical merged reference: `docs\architecture\MAIN.md`

> Canonical reference moved: The authoritative PathAI architecture and implementation blueprint now lives at `docs/architecture/PathAI_Global_Architecture_And_Implementation_Blueprint.md`. This file is preserved as a historical Rebuild-0B archive.

# PathAI Rebuild-0B Architecture, Contracts, And Roadmap

Status: Specification phase  
Project: PathAI  
Target phase: Local no-auth end-to-end demo  
Created: 2026-06-23  

## 1. Executive Summary

Rebuild-0B is the contract-definition phase for the PathAI rebuild. Its purpose is to turn the validated high-level architecture from Rebuild-0A into implementation-ready agreements between the frontend, backend API, service layer, repositories, orchestration layer, agents, RAG subsystem, evaluation subsystem, and database.

Runtime feature implementation must not begin until these contracts are clear because PathAI is a multi-stage AI system. Without explicit workflow state, document schemas, agent input/output contracts, evaluation rules, retry policies, and no-auth demo boundaries, the project can easily become a collection of loosely connected prompts and screens instead of a reliable learning pipeline.

This document defines the first stable implementation target: a local no-auth demo that proves the complete AI learning path loop end to end:

1. A learner creates a learning goal.
2. The system runs a diagnostic assessment.
3. The system builds a knowledge map.
4. The system generates a personalized curriculum.
5. The system attaches curated learning resources.
6. A critic reviews the curriculum.
7. Progress tracking is initialized.
8. A quiz is generated and scored.
9. Weak performance triggers adaptation.
10. The system stores an evaluation report.
11. The frontend displays a learner command center.

The first implementation should optimize for reliability, traceability, deterministic tests, and academic evidence. Production concerns such as authentication, Docker, deployment, CI/CD, hosted multi-user behavior, live web scraping, streaming LLM responses, fine-tuning, and advanced vector infrastructure remain intentionally postponed.


## 1a. Correction Pass Summary

This document has undergone a focused Rebuild-0B correction pass following multiple external reviews. The reviews concluded that the architectural direction is strong and correctly scoped, but identified technical risks around `WorkflowState` bloat, frontend polling mechanics, LLM structured-output reliability, and progress synchronization during replanning.

This pass resolves these implementation blockers by hardening the contracts. It does not redesign the project. The goal is to make the specifications robust enough that Rebuild-1 can begin safely.

## 1b. Implementation Readiness Status

- Rebuild-1 (Backend Foundation and Tooling) may begin after this correction pass is approved.
- Product and business workflow implementation must still wait until Rebuild-2/3 schemas and contracts are implemented and validated.
- This Rebuild-0B phase remains documentation and specification only. No runtime logic has been implemented.

## 2. Current Rebuild State

Rebuild-0A is complete. The project currently has a clean professional foundation and is intentionally free of runtime business logic.

Current known state:

- The project folder structure exists.
- Backend, frontend, docs, data, scripts, tests, infra, reports, and Design folders exist.
- Foundational documentation files exist.
- No backend runtime business logic has been implemented.
- No frontend runtime business logic has been implemented.
- No dependencies have been installed.
- No authentication has been implemented.
- No Docker or deployment work has been implemented.

- The existing `.git` folder is preserved.

Rebuild-0B is documentation and specification only. It must not introduce application runtime behavior.

## 3. Architectural Principles

PathAI follows a clean architecture style adapted for an AI orchestration project.

Core principles:

- The frontend talks only to the backend API.
- Backend API routes call services.
- Services own business logic and application decisions.
- Repositories own persistence abstraction.
- MongoDB stores durable project state.
- Agents do not directly own persistence.
- Agents receive structured inputs and return structured outputs.
- LangGraph coordinates workflow state and node execution, not database storage.
- RAG retrieves and ranks curated learning resources; it does not scrape the live web in v1.
- Evaluation combines deterministic scoring with critic-agent review.
- The local no-auth demo comes before production-grade account management.
- Deterministic tests come before live LLM behavior.
- Mock LLM behavior must allow the main demo path to run without network access.
- Build breadth-first first, then deepen each agent.
- Prefer explicit schemas, typed contracts, and validated outputs over implicit prompt conventions.
- Persist important artifacts only through services and repositories.
- Keep frontend state aligned with backend resource IDs, not hidden local-only state.
- Make the first demo reliable before making it general.

The most important design rule is that agents are not application owners. They are structured transformation components. Services decide when an agent should run, how to validate its output, and what should be saved.


## 3a. Execution Modes

The system operates in two distinct modes. They share the same core services and contracts but differ in input source and orchestration timing.

### Interactive Mode
- Real user manually enters a learning goal.
- User actively answers assessment questions and submits quizzes.
- Frontend shows step-by-step state transitions.
- Backend workflows pause and wait for explicit user actions.

### Deterministic Demo Mode
- Uses a seeded goal and seeded assessment/quiz answers.
- Can run a full no-auth pipeline end-to-end without manual intervention.
- Primarily used for local demo, E2E validation, and academic presentation.
- Must be clearly labeled in the UI as 'Deterministic Demo Mode'.

## 4. System Layering

### 4.1 Primary Product Flow

Layer order:

```text
Frontend
  -> Backend API
    -> Services
      -> Repositories
        -> MongoDB
```

Responsibilities:

- Frontend: renders screens, collects learner input, calls backend endpoints, displays persisted system state.
- Backend API: validates request boundaries, maps HTTP requests to service calls, returns response schemas.
- Services: execute business workflows, enforce rules, coordinate repositories, call orchestration and agents.
- Repositories: provide persistence methods and hide MongoDB implementation details.
- MongoDB: stores durable state for the local demo and later production evolution.

### 4.2 AI Workflow Flow

AI layer order:

```text
Services
  -> LangGraph orchestration
    -> Agents
      -> LLM / RAG / Evaluation logic
```

Responsibilities:

- Services decide when to start or resume a workflow.
- LangGraph coordinates workflow nodes and transitions.
- Agents perform bounded AI tasks with typed inputs and typed outputs.
- LLM client abstracts provider-specific model calls.
- RAG subsystem retrieves and ranks resources from a curated corpus.
- Evaluation subsystem scores artifacts using deterministic rubrics.

### 4.3 Boundary Rules

Frontend must not:

- Connect directly to MongoDB.
- Call LLM providers directly.
- Own core learning-path logic.
- Infer hidden workflow state not returned by the backend.

API routes must not:

- Contain business logic beyond request/response mapping.
- Call MongoDB drivers directly.
- Call LLM clients directly.
- Construct prompts directly.

Services may:

- Coordinate repositories.
- Call orchestration.
- Validate domain rules.
- Decide what to persist.
- Return application-level DTOs to API routes.

Services must not:

- Depend on frontend implementation details.
- Store provider-specific LLM logic.
- Hard-code MongoDB driver calls.

Repositories may:

- Read and write documents.
- Map domain schemas to database documents.
- Enforce simple persistence invariants such as IDs, timestamps, and status updates.

Repositories must not:

- Call agents.
- Call LLMs.
- Decide learning strategy.
- Implement product workflows.

Agents may:

- Generate assessment questions.
- Score answers.
- Build knowledge maps.
- Generate curriculum artifacts.
- Review outputs.
- Produce structured recommendations.

Agents must not:

- Connect to MongoDB.
- Know collection names.
- Commit state.
- Trigger unrelated workflows.
- Return untyped free-form blobs as primary outputs.

LangGraph may:

- Hold and transform workflow state.
- Execute nodes in order.
- Enforce loop caps.
- Route conditional transitions.

LangGraph must not:

- Become the persistence layer.
- Hide important business decisions inside anonymous functions.
- Bypass service-level validation.

## 5. Planned Folder Structure

### 5.1 Backend

```text
backend/app/api/v1
backend/app/core
backend/app/db
backend/app/models
backend/app/schemas
backend/app/repositories
backend/app/services
backend/app/agents
backend/app/orchestration
backend/app/rag
backend/app/evaluation
backend/app/utils
backend/app/tests
```

#### `backend/app/api/v1`

Belongs here:

- FastAPI routers.
- Request and response mapping.
- Endpoint-level dependency injection.
- HTTP status handling.

Does not belong here:

- Prompt construction.
- MongoDB calls.
- workflow graph definitions.
- complex business logic.

#### `backend/app/core`

Belongs here:

- Settings model.
- environment policy.
- logging configuration.
- application constants.
- runtime mode flags.

Does not belong here:

- domain services.
- route handlers.
- agent prompts.

#### `backend/app/db`

Belongs here:

- MongoDB client creation.
- database initialization.
- collection helpers.
- index initialization.

Does not belong here:

- business workflows.
- schema definitions unrelated to persistence.
- prompt logic.

#### `backend/app/models`

Belongs here:

- database document models.
- persistence-facing model definitions.
- common database fields such as IDs, timestamps, version fields, and statuses.

Does not belong here:

- HTTP-only request schemas.
- LLM-only contract schemas unless shared intentionally.

#### `backend/app/schemas`

Belongs here:

- API request schemas.
- API response schemas.
- agent input contracts.
- agent output contracts.
- orchestration state schemas.
- shared domain DTOs.

Does not belong here:

- MongoDB connection code.
- API route implementations.

#### `backend/app/repositories`

Belongs here:

- repository interfaces.
- fake repository implementations for tests and early demo.
- MongoDB repository implementations once persistence stabilizes.

Does not belong here:

- LLM calls.
- graph routing.
- frontend response shaping.

#### `backend/app/services`

Belongs here:

- application business logic.
- orchestration entry points.
- use-case coordination.
- persistence decisions.
- validation of agent outputs before save.

Does not belong here:

- raw HTTP route definitions.
- direct frontend state assumptions.
- provider-specific LLM details.

#### `backend/app/agents`

Belongs here:

- assessment agent.
- knowledge-map agent.
- curriculum agent.
- resource agent.
- critic agent.
- quiz agent.
- adapter agent.
- evaluation agent wrappers if LLM-assisted.
- prompt templates owned by those agents.

Does not belong here:

- persistence code.
- MongoDB collection logic.
- endpoint definitions.

#### `backend/app/orchestration`

Belongs here:

- LangGraph graph definition.
- workflow node functions.
- transition rules.
- workflow state handling.
- graph constants.

Does not belong here:

- MongoDB-specific code.
- frontend-only display logic.
- unconstrained prompt implementations.

#### `backend/app/rag`

Belongs here:

- curated corpus loading.
- resource metadata models.
- ranking functions.
- tag matching.
- later embedding index integration.

Does not belong here:

- live web scraping in v1.
- general service orchestration.
- route handlers.

#### `backend/app/evaluation`

Belongs here:

- scoring rubrics.
- deterministic metrics.
- aggregate PathAI quality score.
- report builders.

Does not belong here:

- persistent database implementation.
- UI-specific formatting.

#### `backend/app/utils`

Belongs here:

- shared helpers that are genuinely cross-cutting.
- ID formatting helpers.
- timestamp helpers.
- safe parsing helpers.

Does not belong here:

- domain logic that should live in services.
- miscellaneous dumping ground code.

#### `backend/app/tests`

Belongs here:

- backend unit tests.
- service tests.
- repository tests.
- orchestration tests.
- agent contract tests with mock LLM outputs.

Does not belong here:

- production code.

### 5.2 Frontend

```text
frontend/app
frontend/components
frontend/components/features
frontend/lib
frontend/styles
frontend/public
```

#### `frontend/app`

Belongs here:

- Next.js app routes.
- route-level layouts.
- page entry points.

Does not belong here:

- reusable business components that belong in `components`.
- backend implementation details.

#### `frontend/components`

Belongs here:

- reusable UI components.
- generic dashboard layout components.
- buttons, panels, progress visualizations, status chips, navigation elements.

Does not belong here:

- route-only data fetching that belongs in app pages.

#### `frontend/components/features`

Belongs here:

- assessment-specific UI modules.
- knowledge map UI modules.
- curriculum UI modules.
- resource list modules.
- quiz modules.
- adaptation modules.
- command-center modules.

Does not belong here:

- generic UI primitives already in `components`.

#### `frontend/lib`

Belongs here:

- API client functions.
- typed response helpers.
- local no-auth ID handling.
- frontend utility functions.

Does not belong here:

- business logic that should be enforced by backend services.

#### `frontend/styles`

Belongs here:

- design tokens.
- global CSS.
- theme variables.

Does not belong here:

- route-specific large component logic.

#### `frontend/public`

Belongs here:

- static images.
- icons.
- public assets.

Does not belong here:

- secrets.
- generated private data.

## 6. Canonical No-Auth Demo Journey

The first demo must be deterministic enough to validate locally and rich enough to demonstrate the full PathAI idea.

Canonical demo goal:

```text
Learn RAG systems for an AI engineering graduation project
```

### 6.1 Learner Profile Assumptions

Draft learner profile:

- Learner type: final-year AI engineering student.
- Existing strengths: Python basics, general machine learning concepts, basic web API knowledge.
- Weak areas: vector search, embedding evaluation, chunking strategy, retrieval metrics, production RAG failure modes.
- Time availability: 6 to 8 hours per week.
- Desired outcome: build and explain a credible RAG subsystem for a graduation project.
- Preferred resource types: documentation, practical tutorials, short papers, implementation examples, and quizzes.
- Difficulty target: intermediate.

### 6.2 Assessment Behavior

Assessment v1 should:

- Ask one question at a time.
- Use a mix of multiple-choice, short-answer, and self-rating questions.
- Start from baseline assumptions for the canonical demo.
- Score each answer into concept evidence.
- Stop when minimum question count and confidence target are satisfied, or when maximum question count is reached.

Draft constants:

```text
MIN_ASSESSMENT_QUESTIONS = 5
MAX_ASSESSMENT_QUESTIONS = 8
KNOWLEDGE_CONFIDENCE_TARGET = 0.75
```

### 6.3 Knowledge Map Output

The knowledge map should classify concepts into:

- strong concepts.
- developing concepts.
- weak concepts.
- missing concepts.

Canonical concepts:

- RAG fundamentals.
- embeddings.
- chunking.
- vector databases.
- retrieval ranking.
- prompt augmentation.
- hallucination reduction.
- evaluation metrics.
- system design.
- FastAPI integration.

### 6.4 Curriculum Output

The first curriculum should be week-by-week, with each week containing topics, outcomes, resource attachments, tasks, and quiz alignment.

Draft duration:

- 4 weeks for the local demo.
- 2 to 4 topics per week.
- 1 quiz checkpoint after the first major module.

### 6.5 Resource Attachment Output

Resources should be attached to topics using a curated seed corpus. Each attachment should include:

- resource ID.
- title.
- type.
- source.
- URL if allowed.
- difficulty.
- estimated minutes.
- relevance score.
- quality score.
- reason for selection.

### 6.6 Critic Review

The critic should evaluate:

- concept coverage.
- difficulty pacing.
- topic sequence.
- resource relevance.
- resource diversity.
- assessment-to-curriculum alignment.
- quiz readiness.

The critic may request revision only within a capped loop.

Draft constants:

```text
MAX_CRITIC_REVISION_ATTEMPTS = 2
CRITIC_PASS_SCORE = 0.80
```

### 6.7 Progress Initialization

The system should initialize:

- goal-level progress.
- topic-level progress.
- current recommended topic.
- weak-topic list.
- upcoming quiz checkpoint.

### 6.8 Quiz Generation

The quiz should:

- target weak or newly taught topics.
- include 5 to 8 questions in the first demo.
- include answer keys.
- include scoring rules.
- map each question to concept IDs.

### 6.9 Quiz Submission

The first demo should support submitting a quiz attempt with deterministic scoring. If the score is below the adaptation threshold, the adapter should run.

Draft constant:

```text
QUIZ_ADAPTATION_THRESHOLD = 0.65
```

### 6.10 Adaptation Trigger

Adaptation should trigger when:

- quiz score is below `QUIZ_ADAPTATION_THRESHOLD`, or
- learner marks the same topic as stuck at least `STUCK_EVENT_THRESHOLD` times.

Draft constant:

```text
STUCK_EVENT_THRESHOLD = 2
```

### 6.11 Evaluation Report

The evaluation report should include:

- metric scores.
- weighted total score.
- pass/fail status.
- warnings.
- recommended next improvements.

### 6.12 Dashboard Display

The command center should show:

- active goal.
- assessment summary.
- knowledge map.
- curriculum timeline.
- recommended next topic.
- attached resources.
- quiz score and weak concepts.
- adaptation event summary if present.
- critic review summary.
- overall PathAI quality score.

## 7. LangGraph Workflow Specification

### 7.1 Workflow Goals

The workflow graph should coordinate the end-to-end demo without hiding domain rules. The first graph should be a straight-line happy path with only bounded loops for assessment, critic revision, and adaptation.

> **Implementation status note (as of Rebuild-22 planning).** `app/orchestration/graph.py` today implements the straight-line happy path, and every node in it calls a real agent through the service layer (`load_assessment` → `agent_services.assessment.run_diagnostic`, `load_curriculum` → `agent_services.curriculum.build`, `load_critic_review` → `agent_services.critic.review`, and so on). It is a single-pass generation pipeline, not an artifact loader.
>
> What it does **not** yet implement are the **bounded loops** specified in §7.3: `should_continue_assessment`, `should_revise_curriculum`, and `should_adapt`. The graph's only conditional edge (`graph.py::_route_after_node`) continues to the next node or stops on failure — there is no re-entry, and `CurriculumAgentInput.critic_recommendations` is always empty with `critic_revision_attempt` fixed at `0`, so the critic's findings never feed back into curriculum generation.
>
> Convergence between `graph.py` and this section's bounded-loop specification is scoped as **Rebuild-23** (see `reports/phases/Plan.md`). It is a graph-shape change (conditional edges and re-entry), not an agent-wiring change, and must not be attempted as a side effect of enabling additional agent flags.

### 7.2 Workflow Constants

```text
MIN_ASSESSMENT_QUESTIONS = 5
MAX_ASSESSMENT_QUESTIONS = 8
KNOWLEDGE_CONFIDENCE_TARGET = 0.75
MAX_CRITIC_REVISION_ATTEMPTS = 2
CRITIC_PASS_SCORE = 0.80
QUIZ_ADAPTATION_THRESHOLD = 0.65
STUCK_EVENT_THRESHOLD = 2
MAX_NODE_RETRIES = 2
LLM_TIMEOUT_SECONDS = 45
```

### 7.3 Graph Nodes

#### `create_goal`

Purpose:

- Validate the learning goal.
- Create a learning goal record through the service and repository layer.
- Initialize workflow IDs and status.

Inputs:

- raw goal text.
- optional learner profile.
- demo mode flag.

Outputs:

- `goal_id`.
- normalized goal.
- initial workflow status.

#### `start_assessment`

Purpose:

- Create an assessment session linked to the goal.
- Initialize assessment counters and concept evidence.

Outputs:

- `assessment_session_id`.
- `assessment_status = "in_progress"`.

#### `generate_question`

Purpose:

- Ask the Assessment Agent for the next question.
- Use existing answers and concept coverage to avoid repetition.

Outputs:

- current assessment question.
- target concept IDs.

#### `score_answer`

Purpose:

- Score the learner answer.
- Update concept evidence.
- Store the answer through service/repository boundaries.

Outputs:

- answer score.
- concept evidence updates.
- updated confidence estimate.

#### `should_continue_assessment`

Purpose:

- Decide whether to ask another question.

Transition logic:

```text
if answered_count < MIN_ASSESSMENT_QUESTIONS:
    go to generate_question
elif confidence < KNOWLEDGE_CONFIDENCE_TARGET and answered_count < MAX_ASSESSMENT_QUESTIONS:
    go to generate_question
else:
    go to build_knowledge_map
```

#### `build_knowledge_map`

Purpose:

- Convert assessment evidence into concept mastery classifications.
- Persist knowledge map.

Outputs:

- `knowledge_map_id`.
- concept mastery list.

#### `generate_curriculum`

Purpose:

- Generate week-by-week curriculum from goal and knowledge map.
- Persist draft curriculum.

Outputs:

- `curriculum_id`.
- curriculum weeks and topics.

#### `attach_resources`

Purpose:

- Retrieve and rank curated resources for curriculum topics.
- Attach resources to topic IDs.

Outputs:

- resource attachments.
- resource coverage warnings.

#### `critic_review`

Purpose:

- Evaluate curriculum quality.
- Decide whether revision is needed.

Outputs:

- critic review.
- critic score.
- revision recommendations.

#### `should_revise_curriculum`

Purpose:

- Decide whether to revise curriculum based on critic review.

Transition logic:

```text
if critic_score >= CRITIC_PASS_SCORE:
    go to initialize_progress
elif critic_revision_attempts >= MAX_CRITIC_REVISION_ATTEMPTS:
    go to initialize_progress with warning
else:
    increment critic_revision_attempts
    go to generate_curriculum with critic recommendations
```

#### `initialize_progress`

Purpose:

- Initialize learner progress from accepted curriculum.

Outputs:

- `progress_state_id`.
- topic progress rows.

#### `generate_quiz`

Purpose:

- Generate first checkpoint quiz.
- Persist quiz.

Outputs:

- `quiz_id`.
- quiz questions.

#### `score_quiz`

Purpose:

- Score submitted quiz attempt.
- Persist quiz attempt.
- Update topic progress and weak concepts.

Outputs:

- `quiz_attempt_id`.
- score.
- weak concept IDs.

#### `should_adapt`

Purpose:

- Decide whether curriculum adaptation is needed.

Transition logic:

```text
if quiz_score < QUIZ_ADAPTATION_THRESHOLD:
    go to adapt_curriculum
elif repeated_stuck_count >= STUCK_EVENT_THRESHOLD:
    go to adapt_curriculum
else:
    go to evaluate_run
```

#### `adapt_curriculum`

Purpose:

- Produce a bounded plan revision for weak topics.
- Persist adaptation event.

Outputs:

- `adaptation_event_id`.
- before/after changes.
- updated topic plan.

#### `evaluate_run`

Purpose:

- Compute deterministic metrics and optional critic-assisted summary.
- Persist evaluation report.

Outputs:

- `evaluation_report_id`.
- overall PathAI score.

#### `persist_run`

Purpose:

- Persist orchestration run summary, node statuses, warnings, and final result IDs.

Outputs:

- `orchestration_run_id`.
- final workflow status.

#### `prepare_dashboard_payload`

Purpose:

- Build a stable response payload for the frontend command center.

Outputs:

- dashboard payload DTO.

### 7.4 Graph Edges

Primary straight-line edges:

```text
create_goal -> start_assessment
start_assessment -> generate_question
generate_question -> score_answer
score_answer -> should_continue_assessment
should_continue_assessment -> generate_question
should_continue_assessment -> build_knowledge_map
build_knowledge_map -> generate_curriculum
generate_curriculum -> attach_resources
attach_resources -> critic_review
critic_review -> should_revise_curriculum
should_revise_curriculum -> generate_curriculum
should_revise_curriculum -> initialize_progress
initialize_progress -> generate_quiz
generate_quiz -> score_quiz
score_quiz -> should_adapt
should_adapt -> adapt_curriculum
should_adapt -> evaluate_run
adapt_curriculum -> evaluate_run
evaluate_run -> persist_run
persist_run -> prepare_dashboard_payload
```

### 7.5 Failure Behavior

Each node should return a structured node result:

- `status`: `success`, `failed`, `skipped`, or `requires_input`.
- `errors`: list of structured errors.
- `warnings`: list of recoverable issues.
- `retryable`: boolean.

Failure policy:

- Validation failure: do not retry automatically; return actionable error.
- LLM timeout: retry up to `MAX_NODE_RETRIES`.
- malformed LLM output: retry with repair prompt once, then fallback to mock or deterministic fallback if in demo mode.
- RAG no results: continue with warning and placeholder attachment candidates from seed corpus if available.
- critic failure: continue with deterministic evaluation warning after retry cap.
- database write failure: fail the workflow node and return error; do not pretend persistence succeeded.

### 7.6 Retry Behavior

Retry metadata must be stored in workflow state:

- node name.
- attempt count.
- last error code.
- last error message.
- retry timestamp.

Retries should not duplicate persisted records. Services should use idempotency keys or check for existing records by `run_id`, `goal_id`, and node name where appropriate.

### 7.7 Restart And Resume For V1

For v1 local no-auth demo:

- Full durable resume is postponed.
- The system should persist `OrchestrationRun` and node events for auditability.
- If a workflow fails, the user can restart the demo run from the latest persisted major artifact where supported.
- Fine-grained graph checkpoint resume can be added after the no-auth demo works.

### 7.8 Multi-Agent Execution Policy

Status: **approved direction, not yet implemented.** The enforcement rules corresponding to this policy are `RULES.md` §17. Nothing described in this subsection exists in `app/` today.

#### 7.8.1 Current State

Nine agent roles run in every orchestration run, but only four have any LLM-backed implementation (`app/agents/llm/`): Assessment, Knowledge Map, Critic, Curriculum. The remaining five (Resource, Progress, Quiz, Adaptation, Evaluation) are deterministic-only, with no LLM path scaffolded.

`resolve_agent_integration_switches` (`app/agents/services/activation/switches.py`) currently hard-enforces **at most one** LLM-backed agent per process, raising `ActivationConfigError` if two or more `PATHAI_ENABLE_LLM_*_AGENT` flags are set. This is a deliberate rollout-safety gate introduced in Rebuild-14B, not an architectural ceiling: the agent classes are independent objects and nothing in them prevents concurrent use.

The practical consequence is that PathAI today is **not** a multi-agent AI system. Every run is one real-AI agent embedded in an otherwise deterministic pipeline. The system is a multi-agent *architecture* (nine separately-contracted roles), which is a different claim and should not be conflated with it in any document.

#### 7.8.2 Definition Of Multi-Agent

A run qualifies as multi-agent only if all five conditions in `RULES.md` §17.1 hold: two or more LLM-backed agents in the same run; a real data dependency between them; reachability over HTTP; per-run observability and a hard bound; and validation of the specific combination. Falling short on any of points 2 through 5 makes a run parallel single-agent activation, not a multi-agent platform.

#### 7.8.3 Validated-Combination Allowlist

The binary one-at-a-time gate is to be replaced by a graduated, code-defined allowlist of validated combinations, per `RULES.md` §17.2. Zero or one enabled LLM agent remains allowed unconditionally. A set of two or more is admitted only once that exact combination has a phase, an interaction test, and a recap behind it. Unlisted combinations continue to fail loudly at construction time.

This is deliberately not a flag flip. Removing the gate wholesale would trade a safe-but-limited system for an unvalidated one, and would reintroduce — at the combination level — the precise defect Rebuild-14D shipped and later corrected, in which per-agent flags silently activated a real, never-integration-tested LLM agent.

#### 7.8.4 First Target Combination: Curriculum → Critic

The Curriculum→Critic handoff is the natural first validated combination because the data dependency **already exists structurally in the current graph**. `load_curriculum` persists the curriculum agent's output through `CurriculumAgentService`; `load_critic_review` reads that persisted curriculum back and passes it into the critic agent. Enabling both in LLM mode therefore produces a genuine LLM→LLM handoff with no graph change required — only the allowlist and an interaction test proving the critic consumed the curriculum agent's real output rather than a deterministic fixture.

The reverse direction, Critic→Curriculum feedback, does **not** exist and cannot be added this way. It requires the bounded `should_revise_curriculum` loop from §7.3 — a graph-shape change, scoped separately as Rebuild-23 (§7.1's implementation status note).

#### 7.8.5 Run-Level Budget

Rebuild-15 bounded reliability per agent: retry caps, bounded backoff, timeout policy, and a sanitized `LLMReliabilityObserver` event stream. Once two or more agents chain real LLM calls inside one run, that per-agent bound is no longer sufficient — nothing constrains the run as a whole.

A run-level budget is therefore a prerequisite for any allowlisted combination: a maximum total LLM call count and a maximum wall-clock duration per run, enforced above and independently of any single agent's retry policy, failing safe to deterministic fallback rather than hard-failing the run, and emitting a sanitized, observable event on exhaustion. It aggregates the existing per-agent observer stream rather than replacing it.

Note the boundary constraint this imposes: `app/orchestration/` must not import `app.llm` (standing scope-security audit). A run-scoped observer must therefore be constructed inside the activation factory (`build_injected_agents`), which orchestration already calls legitimately, and any helper that itself imports `app.llm` belongs under `app/agents/llm/` — the only allowlisted directory for that import.

#### 7.8.6 Sequencing

Per-run budget primitives land first, inert and called by nothing. The budget is then wired into a run. Only then does the first validated combination open. Each step is its own phase with its own recap, following the same safest-first discipline used for the single-agent rollout in Rebuild-14D/14F/14G and Rebuild-15A–D. Combination phases can be validated test-only ahead of RAG (Rebuild-16) and persistence (Rebuild-17); HTTP reachability — condition 3 of §7.8.2 — remains blocked on Rebuild-18, which adds the first route that triggers orchestration at all.


## 8. WorkflowState Schema

The `WorkflowState` must be lightweight. It should store IDs, statuses, current step, counters, summaries, and error metadata. **Avoid storing huge nested full documents inside the graph state.** Full documents must live in repositories. Graph nodes fetch needed objects through services/repositories. This prevents state bloat, checkpoint bloat, and accidental giant LLM prompts.

```python
class WorkflowState(BaseModel):
    run_id: str
    goal_id: str | None = None
    assessment_session_id: str | None = None
    knowledge_map_id: str | None = None
    curriculum_id: str | None = None
    progress_state_id: str | None = None
    quiz_id: str | None = None
    quiz_attempt_id: str | None = None
    adaptation_event_ids: list[str] = []
    critic_review_id: str | None = None
    evaluation_report_id: str | None = None
    
    current_node: str | None = None
    status: Literal["queued", "running", "waiting_for_user", "completed", "failed", "cancelled"]
    mode: Literal["interactive", "demo"] = "interactive"
    pending_user_action: str | None = None
    
    assessment_question_count: int = 0
    assessment_confidence: float = 0.0
    critic_revision_attempts: int = 0
    repeated_stuck_count: int = 0
    quiz_score: float | None = None
    
    errors: list[WorkflowError] = []
    warnings: list[WorkflowWarning] = []
    node_attempts: dict[str, int] = {}
    
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    
    trace_metadata: dict[str, Any] = {}
```
## 9. Agent Contracts

All agents must accept typed inputs and return typed outputs. Agent output must validate before services persist it.

### 9.1 Assessment Agent

Purpose:

- Generate diagnostic questions.
- Score learner answers.
- Update concept evidence.

Input contract:

```python
class AssessmentAgentInput(BaseModel):
    goal_text: str
    learner_profile: LearnerProfile
    prior_answers: list[AssessmentAnswerDTO]
    target_concepts: list[str]
    current_confidence: float
    question_count: int
```

Output contract:

```python
class AssessmentAgentOutput(BaseModel):
    question: AssessmentQuestionDTO
    rationale: str
    estimated_information_gain: float
```

Answer scoring output:

```python
class AssessmentScoreOutput(BaseModel):
    answer_id: str | None
    score: float
    concept_scores: list[ConceptEvidenceUpdate]
    feedback: str
    confidence_after_answer: float
```

Validation rules:

- Question text is required.
- Question type must be one of `multiple_choice`, `short_answer`, or `self_rating`.
- Target concepts must not be empty.
- Scores must be between 0.0 and 1.0.

Failure output:

```json
{
  "status": "failed",
  "error_code": "assessment_generation_failed",
  "message": "Could not generate a valid assessment question."
}
```

Mock output expectation:

- For the canonical demo, mock output returns deterministic RAG-related questions.

Example output:

```json
{
  "question": {
    "question_id": "q_demo_001",
    "question_type": "multiple_choice",
    "prompt": "Which component is primarily responsible for finding relevant documents in a RAG pipeline?",
    "options": ["Retriever", "Tokenizer", "Optimizer", "Frontend router"],
    "target_concepts": ["retrieval", "rag_fundamentals"],
    "difficulty": "beginner"
  },
  "rationale": "The question checks whether the learner understands the retrieval role in RAG.",
  "estimated_information_gain": 0.72
}
```

### 9.2 Knowledge Map Agent

Purpose:

- Convert assessment evidence into concept mastery classifications.

Input contract:

```python
class KnowledgeMapAgentInput(BaseModel):
    goal_text: str
    assessment_answers: list[AssessmentAnswerDTO]
    concept_evidence: list[ConceptEvidence]
```

Output contract:

```python
class KnowledgeMapAgentOutput(BaseModel):
    concepts: list[ConceptMasteryDTO]
    strong_concepts: list[str]
    developing_concepts: list[str]
    weak_concepts: list[str]
    missing_concepts: list[str]
    confidence: float
    summary: str
```

Validation rules:

- At least one concept must be returned.
- Every concept must have a mastery score between 0.0 and 1.0.
- Every concept must have a classification.

Failure output:

```json
{
  "status": "failed",
  "error_code": "knowledge_map_generation_failed",
  "message": "Could not build a valid knowledge map."
}
```

Mock output expectation:

- Deterministic classification showing Python/API as stronger and vector search/evaluation as weaker.

Example output:

```json
{
  "concepts": [
    {
      "concept_id": "rag_fundamentals",
      "label": "RAG fundamentals",
      "mastery_score": 0.78,
      "classification": "strong",
      "evidence": ["Correctly identified retriever role."]
    },
    {
      "concept_id": "retrieval_evaluation",
      "label": "Retrieval evaluation",
      "mastery_score": 0.28,
      "classification": "weak",
      "evidence": ["Could not distinguish recall@k from answer quality."]
    }
  ],
  "strong_concepts": ["rag_fundamentals"],
  "developing_concepts": ["chunking"],
  "weak_concepts": ["retrieval_evaluation"],
  "missing_concepts": ["reranking"],
  "confidence": 0.77,
  "summary": "The learner understands high-level RAG but needs support with retrieval quality and evaluation."
}
```

### 9.3 Curriculum Agent

Purpose:

- Generate a structured week-by-week plan aligned to the knowledge map.

Input contract:

```python
class CurriculumAgentInput(BaseModel):
    goal_text: str
    learner_profile: LearnerProfile
    knowledge_map: KnowledgeMapDTO
    duration_weeks: int
    hours_per_week: int
    critic_recommendations: list[str] = []
```

Output contract:

```python
class CurriculumAgentOutput(BaseModel):
    title: str
    duration_weeks: int
    weeks: list[CurriculumWeekDTO]
    assumptions: list[str]
    target_outcomes: list[str]
```

Validation rules:

- `duration_weeks` must equal number of weeks.
- Each week must contain at least one topic.
- Each topic must map to at least one concept ID.
- Difficulty must be one of `beginner`, `intermediate`, `advanced`.

Failure output:

```json
{
  "status": "failed",
  "error_code": "curriculum_generation_failed",
  "message": "Could not generate a valid curriculum."
}
```

Mock output expectation:

- Four-week deterministic curriculum for RAG graduation project.

Example output:

```json
{
  "title": "Four-Week RAG Systems Build Plan",
  "duration_weeks": 4,
  "weeks": [
    {
      "week_number": 1,
      "theme": "RAG foundations and retrieval basics",
      "topics": [
        {
          "topic_id": "topic_retrieval_basics",
          "title": "Retriever role and document grounding",
          "concept_ids": ["rag_fundamentals", "retrieval"],
          "difficulty": "beginner",
          "estimated_hours": 3,
          "learning_outcomes": ["Explain how retrieval augments generation."]
        }
      ]
    }
  ],
  "assumptions": ["The learner can write Python functions and call APIs."],
  "target_outcomes": ["Design a small RAG subsystem and evaluate retrieval quality."]
}
```

### 9.4 Resource/RAG Agent

Purpose:

- Attach curated resources to curriculum topics using metadata ranking in v1.

Input contract:

```python
class ResourceAgentInput(BaseModel):
    curriculum: CurriculumDTO
    knowledge_map: KnowledgeMapDTO
    corpus_resources: list[ResourceDTO]
    max_resources_per_topic: int = 3
```

Output contract:

```python
class ResourceAgentOutput(BaseModel):
    attachments: list[ResourceAttachmentDTO]
    coverage_summary: ResourceCoverageSummary
    warnings: list[str]
```

Validation rules:

- Every attachment must reference a valid topic ID and resource ID.
- Relevance score and quality score must be between 0.0 and 1.0.
- Resource type must be allowed by the corpus schema.

Failure output:

```json
{
  "status": "failed",
  "error_code": "resource_attachment_failed",
  "message": "Could not attach valid resources."
}
```

Mock output expectation:

- Deterministic resources from the seed corpus with topic tags and relevance reasons.

Example output:

```json
{
  "attachments": [
    {
      "attachment_id": "attach_001",
      "topic_id": "topic_retrieval_basics",
      "resource_id": "res_rag_intro_001",
      "rank": 1,
      "relevance_score": 0.91,
      "selection_reason": "Matches retrieval and RAG fundamentals tags at beginner difficulty."
    }
  ],
  "coverage_summary": {
    "topics_with_resources": 1,
    "topics_without_resources": 0,
    "average_relevance": 0.91,
    "resource_type_diversity": 0.67
  },
  "warnings": []
}
```

### 9.5 Critic Agent

Purpose:

- Review curriculum quality and recommend bounded revisions.

Input contract:

```python
class CriticAgentInput(BaseModel):
    goal_text: str
    knowledge_map: KnowledgeMapDTO
    curriculum: CurriculumDTO
    resource_attachments: list[ResourceAttachmentDTO]
    rubric_weights: dict[str, float]
```

Output contract:

```python
class CriticAgentOutput(BaseModel):
    overall_score: float
    pass_status: Literal["pass", "revise", "pass_with_warnings"]
    dimension_scores: dict[str, float]
    strengths: list[str]
    issues: list[str]
    revision_recommendations: list[str]
```

Validation rules:

- Overall score must be between 0.0 and 1.0.
- Dimension scores must match known rubric dimensions.
- Revision recommendations must be actionable and bounded.

Failure output:

```json
{
  "status": "failed",
  "error_code": "critic_review_failed",
  "message": "Could not complete critic review."
}
```

Mock output expectation:

- First pass may return one or two improvement suggestions; second pass should pass for canonical demo.

Example output:

```json
{
  "overall_score": 0.84,
  "pass_status": "pass",
  "dimension_scores": {
    "coverage": 0.86,
    "pacing": 0.82,
    "resource_relevance": 0.88,
    "assessment_alignment": 0.80
  },
  "strengths": ["Weak retrieval-evaluation concepts are addressed before final project integration."],
  "issues": ["Week 2 may need one extra practical exercise."],
  "revision_recommendations": []
}
```

### 9.6 Quiz Agent

Purpose:

- Generate and score quizzes linked to curriculum topics and concept IDs.

Input contract:

```python
class QuizAgentInput(BaseModel):
    goal_text: str
    curriculum_topics: list[CurriculumTopicDTO]
    target_concepts: list[str]
    difficulty: str
    question_count: int
```

Output contract:

```python
class QuizAgentOutput(BaseModel):
    quiz_title: str
    questions: list[QuizQuestionDTO]
    scoring_policy: QuizScoringPolicy
```

Scoring output:

```python
class QuizScoreOutput(BaseModel):
    total_score: float
    correct_count: int
    total_questions: int
    concept_scores: list[ConceptQuizScore]
    weak_concepts: list[str]
    feedback: str
```

Validation rules:

- Every question must have concept IDs.
- Multiple-choice questions must include options and correct answer.
- Score must be normalized between 0.0 and 1.0.

Failure output:

```json
{
  "status": "failed",
  "error_code": "quiz_generation_failed",
  "message": "Could not generate a valid quiz."
}
```

Mock output expectation:

- Deterministic quiz with answer key for canonical RAG topics.

Example output:

```json
{
  "quiz_title": "RAG Retrieval Checkpoint",
  "questions": [
    {
      "question_id": "quiz_q_001",
      "question_type": "multiple_choice",
      "prompt": "What does recall@k measure in retrieval evaluation?",
      "options": [
        "Whether relevant items appear in the top k retrieved results",
        "Whether the model response is fluent",
        "How many tokens the model generated",
        "How fast the frontend loads"
      ],
      "correct_answer": "Whether relevant items appear in the top k retrieved results",
      "concept_ids": ["retrieval_evaluation"],
      "difficulty": "intermediate"
    }
  ],
  "scoring_policy": {
    "type": "exact_match",
    "partial_credit": false
  }
}
```

### 9.7 Adapter/Replanning Agent

Purpose:

- Modify the curriculum when weak areas are detected.

Input contract:

```python
class AdapterAgentInput(BaseModel):
    goal_text: str
    curriculum: CurriculumDTO
    progress_state: ProgressStateDTO
    quiz_attempt: QuizAttemptDTO | None
    weak_concepts: list[str]
    stuck_events: list[StuckEventDTO]
```

Output contract:

```python
class AdapterAgentOutput(BaseModel):
    trigger_reason: str
    before_summary: str
    after_summary: str
    changes: list[CurriculumChangeDTO]
    added_practice_topics: list[CurriculumTopicDTO]
    removed_or_deferred_topics: list[str]
    expected_benefit: str
```

Validation rules:

- Every change must reference an existing curriculum ID or topic ID where applicable.
- Adaptation must not delete the whole curriculum.
- Adaptation must include before/after summary.

Failure output:

```json
{
  "status": "failed",
  "error_code": "adaptation_failed",
  "message": "Could not generate a valid adaptation."
}
```

Mock output expectation:

- If quiz score is low on retrieval evaluation, add a remedial topic and one extra practice quiz.

Example output:

```json
{
  "trigger_reason": "quiz_score_below_threshold",
  "before_summary": "The learner moved from RAG foundations to evaluation too quickly.",
  "after_summary": "The plan adds retrieval metrics practice before project integration.",
  "changes": [
    {
      "change_type": "insert_topic",
      "target_week": 2,
      "reason": "Weak score on retrieval_evaluation",
      "topic_title": "Practice recall@k and precision@k with toy retrieval results"
    }
  ],
  "added_practice_topics": [],
  "removed_or_deferred_topics": [],
  "expected_benefit": "The learner should understand how to measure retriever quality before tuning the RAG pipeline."
}
```

### 9.8 Evaluation Agent

Purpose:

- Produce a structured evaluation report using deterministic metrics and optional narrative review.

Input contract:

```python
class EvaluationAgentInput(BaseModel):
    goal: LearningGoalDTO
    assessment: AssessmentSessionDTO
    knowledge_map: KnowledgeMapDTO
    curriculum: CurriculumDTO
    resources: list[ResourceAttachmentDTO]
    critic_review: CriticReviewDTO | None
    quiz_attempt: QuizAttemptDTO | None
    adaptation_event: AdaptationEventDTO | None
```

Output contract:

```python
class EvaluationAgentOutput(BaseModel):
    metric_scores: dict[str, float]
    weighted_score: float
    pass_status: Literal["pass", "fail", "pass_with_warnings"]
    warnings: list[str]
    recommendations: list[str]
```

Validation rules:

- All metric scores must be normalized between 0.0 and 1.0.
- Weighted score must match configured weights.
- Pass status must follow threshold rules.

Failure output:

```json
{
  "status": "failed",
  "error_code": "evaluation_failed",
  "message": "Could not generate evaluation report."
}
```

Mock output expectation:

- Deterministic weighted score computed from stored artifacts.

## 10. MongoDB Document Schemas

General document conventions:

- IDs should be stable strings at the domain layer.
- MongoDB `_id` may be ObjectId internally, but API-facing IDs should be stringified.
- All documents include `created_at`, `updated_at`, and `schema_version`.
- Major workflow documents include `run_id` where relevant.
- Status fields use controlled vocabularies.
- Store generated artifacts with enough metadata for auditability.

### 10.1 LearningGoal

Purpose:

- Represents the learner's target outcome.

Required fields:

- `_id`
- `goal_id`
- `run_id`
- `goal_text`
- `normalized_goal_text`
- `status`
- `learner_profile`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `constraints`
- `target_duration_weeks`
- `hours_per_week`
- `demo_seed_id`
- `metadata`

Indexes:

- unique `goal_id`
- `run_id`
- `status`
- `created_at`

Status values:

- `created`
- `assessment_started`
- `curriculum_generated`
- `active`
- `completed`
- `failed`

Relationships:

- One goal has one or more assessment sessions.
- One goal has one primary knowledge map.
- One goal has one active curriculum.
- One goal has one progress state.

Embed vs reference:

- Embed small learner profile.
- Reference assessment, curriculum, progress, and reports by IDs.

Repository owner:

- `LearningGoalRepository`

### 10.2 AssessmentSession

Purpose:

- Tracks diagnostic assessment lifecycle.

Required fields:

- `_id`
- `assessment_session_id`
- `goal_id`
- `run_id`
- `status`
- `question_count`
- `confidence`
- `concept_evidence`
- `started_at`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `completed_at`
- `termination_reason`
- `metadata`

Indexes:

- unique `assessment_session_id`
- `goal_id`
- `run_id`
- `status`

Status values:

- `created`
- `in_progress`
- `completed`
- `failed`

Relationships:

- Belongs to one learning goal.
- Has many assessment answers.

Embed vs reference:

- Reference answers as separate documents for auditability.
- Embed compact concept evidence summary.

Repository owner:

- `AssessmentRepository`

### 10.3 AssessmentAnswer

Purpose:

- Stores one assessment question, learner answer, and score.

Required fields:

- `_id`
- `answer_id`
- `assessment_session_id`
- `goal_id`
- `question`
- `answer`
- `score`
- `concept_scores`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `feedback`
- `llm_trace_id`
- `metadata`

Indexes:

- unique `answer_id`
- `assessment_session_id`
- `goal_id`
- `created_at`

Status values:

- not required unless answer review workflow is added.

Relationships:

- Belongs to one assessment session.

Embed vs reference:

- Separate document to preserve full answer history.

Repository owner:

- `AssessmentRepository`

### 10.4 KnowledgeMap

Purpose:

- Stores concept mastery inferred from assessment.

Required fields:

- `_id`
- `knowledge_map_id`
- `goal_id`
- `assessment_session_id`
- `run_id`
- `status`
- `concepts`
- `strong_concepts`
- `developing_concepts`
- `weak_concepts`
- `missing_concepts`
- `confidence`
- `summary`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `generation_metadata`
- `warnings`

Indexes:

- unique `knowledge_map_id`
- `goal_id`
- `assessment_session_id`
- `run_id`

Status values:

- `draft`
- `active`
- `superseded`
- `failed`

Relationships:

- Belongs to one goal and assessment session.
- Used by curriculum generation.

Embed vs reference:

- Embed `ConceptMastery` entries because they are read as one map.

Repository owner:

- `KnowledgeMapRepository`

### 10.5 ConceptMastery

Purpose:

- Represents mastery for a single concept inside a knowledge map.

Required fields:

- `concept_id`
- `label`
- `mastery_score`
- `classification`
- `evidence`

Optional fields:

- `prerequisites`
- `recommended_action`
- `confidence`

Indexes:

- no standalone collection index if embedded.
- if extracted later, index `concept_id` and `goal_id`.

Status values:

- not required.

Relationships:

- Embedded in KnowledgeMap.

Embed vs reference:

- Embed in KnowledgeMap for v1.

Repository owner:

- `KnowledgeMapRepository`

### 10.6 Curriculum

Purpose:

- Stores a generated learning plan.

Required fields:

- `_id`
- `curriculum_id`
- `goal_id`
- `knowledge_map_id`
- `run_id`
- `status`
- `title`
- `duration_weeks`
- `weeks`
- `target_outcomes`
- `assumptions`
- `critic_revision_attempt`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `critic_review_ids`
- `adaptation_event_ids`
- `generation_metadata`
- `warnings`

Indexes:

- unique `curriculum_id`
- `goal_id`
- `knowledge_map_id`
- `run_id`
- `status`

Status values:

- `draft`
- `under_review`
- `active`
- `adapted`
- `superseded`
- `failed`

Relationships:

- Belongs to one goal and knowledge map.
- Has embedded weeks and topics.
- Has resource attachments by topic.

Embed vs reference:

- Embed weeks and topics for v1 because curriculum is usually loaded as one artifact.
- Reference resource documents and attach by IDs.

Repository owner:

- `CurriculumRepository`

### 10.7 CurriculumWeek

Purpose:

- Represents one week of the curriculum.

Required fields:

- `week_id`
- `week_number`
- `theme`
- `topics`
- `estimated_hours`
- `learning_outcomes`

Optional fields:

- `milestone`
- `notes`

Indexes:

- embedded, no standalone index.

Status values:

- not required in v1.

Relationships:

- Embedded in Curriculum.

Embed vs reference:

- Embed in Curriculum.

Repository owner:

- `CurriculumRepository`

### 10.8 CurriculumTopic

Purpose:

- Represents one learnable topic inside a curriculum week.

Required fields:

- `topic_id`
- `title`
- `description`
- `concept_ids`
- `difficulty`
- `estimated_hours`
- `learning_outcomes`
- `sequence_order`

Optional fields:

- `practice_task`
- `assessment_checkpoint`
- `resource_attachment_ids`
- `adaptation_origin`

Indexes:

- embedded in v1.
- if extracted later, index `topic_id`, `curriculum_id`, and `concept_ids`.

Status values:

- not required in curriculum document; progress status lives in `TopicProgress`.

Relationships:

- Embedded in CurriculumWeek.
- Referenced by ResourceAttachment and TopicProgress.

Embed vs reference:

- Embed in Curriculum.

Repository owner:

- `CurriculumRepository`

### 10.9 Resource

Purpose:

- Stores curated learning-resource metadata.

Required fields:

- `_id`
- `resource_id`
- `title`
- `resource_type`
- `source_name`
- `url`
- `topic_tags`
- `concept_ids`
- `difficulty`
- `estimated_minutes`
- `quality_score`
- `license_note`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `summary`
- `author`
- `published_year`
- `language`
- `embedding_id`
- `metadata`

Indexes:

- unique `resource_id`
- `topic_tags`
- `concept_ids`
- `difficulty`
- `quality_score`
- text index on `title` and `summary` if useful.

Status values:

- `active`
- `deprecated`
- `needs_review`

Relationships:

- Referenced by ResourceAttachment.

Embed vs reference:

- Standalone collection because resources can be reused across goals.

Repository owner:

- `ResourceRepository`

### 10.10 ResourceAttachment

Purpose:

- Links a resource to a curriculum topic with ranking metadata.

Required fields:

- `_id`
- `attachment_id`
- `goal_id`
- `curriculum_id`
- `topic_id`
- `resource_id`
- `rank`
- `relevance_score`
- `selection_reason`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `quality_score_snapshot`
- `diversity_category`
- `warnings`

Indexes:

- unique `attachment_id`
- `curriculum_id`
- `topic_id`
- `resource_id`
- compound `curriculum_id + topic_id + rank`

Status values:

- `active`
- `superseded`
- `removed`

Relationships:

- Belongs to curriculum topic.
- References Resource.

Embed vs reference:

- Separate document for easier updates and reuse.

Repository owner:

- `ResourceRepository`

### 10.11 ProgressState

Purpose:

- Tracks learner progress for a goal and curriculum.

Required fields:

- `_id`
- `progress_state_id`
- `goal_id`
- `curriculum_id`
- `status`
- `overall_completion`
- `current_topic_id`
- `topic_progress`
- `weak_concepts`
- `stuck_events`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `last_activity_at`
- `next_recommended_action`
- `metadata`

Indexes:

- unique `progress_state_id`
- `goal_id`
- `curriculum_id`
- `status`

Status values:

- `not_started`
- `in_progress`
- `adaptation_needed`
- `completed`

Relationships:

- Belongs to one goal and one active curriculum.

Embed vs reference:

- Embed topic progress for v1 because it is dashboard-read heavy.

Repository owner:

- `ProgressRepository`

### 10.12 TopicProgress

Purpose:

- Tracks completion and status for a curriculum topic.

Required fields:

- `topic_id`
- `status`
- `completion`
- `last_score`
- `attempt_count`

Optional fields:

- `completed_at`
- `stuck_count`
- `notes`

Indexes:

- embedded in ProgressState for v1.

Status values:

- `not_started`
- `in_progress`
- `completed`
- `stuck`
- `needs_review`

Relationships:

- Embedded in ProgressState.

Embed vs reference:

- Embed in ProgressState.

Repository owner:

- `ProgressRepository`

### 10.13 Quiz

Purpose:

- Stores generated quiz questions and answer key.

Required fields:

- `_id`
- `quiz_id`
- `goal_id`
- `curriculum_id`
- `target_topic_ids`
- `target_concept_ids`
- `status`
- `title`
- `questions`
- `scoring_policy`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `difficulty`
- `generation_metadata`

Indexes:

- unique `quiz_id`
- `goal_id`
- `curriculum_id`
- `status`

Status values:

- `draft`
- `active`
- `completed`
- `archived`

Relationships:

- Belongs to goal and curriculum.
- Has many attempts.

Embed vs reference:

- Embed QuizQuestion entries in Quiz.

Repository owner:

- `QuizRepository`

### 10.14 QuizQuestion

Purpose:

- Represents one quiz question.

Required fields:

- `question_id`
- `question_type`
- `prompt`
- `concept_ids`
- `difficulty`
- `correct_answer`
- `points`

Optional fields:

- `options`
- `rubric`
- `explanation`

Indexes:

- embedded in Quiz for v1.

Status values:

- not required.

Relationships:

- Embedded in Quiz.

Embed vs reference:

- Embed in Quiz.

Repository owner:

- `QuizRepository`

### 10.15 QuizAttempt

Purpose:

- Stores learner answers and quiz score.

Required fields:

- `_id`
- `quiz_attempt_id`
- `quiz_id`
- `goal_id`
- `curriculum_id`
- `answers`
- `total_score`
- `correct_count`
- `total_questions`
- `concept_scores`
- `weak_concepts`
- `submitted_at`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `feedback`
- `adaptation_triggered`
- `metadata`

Indexes:

- unique `quiz_attempt_id`
- `quiz_id`
- `goal_id`
- `submitted_at`

Status values:

- `submitted`
- `scored`
- `failed`

Relationships:

- Belongs to Quiz.
- May trigger AdaptationEvent.

Embed vs reference:

- Separate document for attempt history.

Repository owner:

- `QuizRepository`

### 10.16 AdaptationEvent

Purpose:

- Stores curriculum replanning event and before/after changes.

Required fields:

- `_id`
- `adaptation_event_id`
- `goal_id`
- `curriculum_id`
- `trigger_type`
- `trigger_details`
- `before_summary`
- `after_summary`
- `changes`
- `status`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `quiz_attempt_id`
- `stuck_event_ids`
- `new_curriculum_id`
- `metadata`

Indexes:

- unique `adaptation_event_id`
- `goal_id`
- `curriculum_id`
- `trigger_type`
- `created_at`

Status values:

- `proposed`
- `applied`
- `failed`

Relationships:

- Belongs to goal and curriculum.
- May reference quiz attempt.

Embed vs reference:

- Separate document for auditability.

Repository owner:

- `AdaptationRepository`

### 10.17 CriticReview

Purpose:

- Stores critic review for curriculum and resources.

Required fields:

- `_id`
- `critic_review_id`
- `goal_id`
- `curriculum_id`
- `run_id`
- `overall_score`
- `pass_status`
- `dimension_scores`
- `strengths`
- `issues`
- `revision_recommendations`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `revision_attempt`
- `metadata`

Indexes:

- unique `critic_review_id`
- `goal_id`
- `curriculum_id`
- `run_id`
- `pass_status`

Status values:

- `pass`
- `revise`
- `pass_with_warnings`
- `failed`

Relationships:

- Belongs to curriculum.

Embed vs reference:

- Separate document to track revision history.

Repository owner:

- `CriticReviewRepository`

### 10.18 EvaluationReport

Purpose:

- Stores system quality evaluation for a run or goal.

Required fields:

- `_id`
- `evaluation_report_id`
- `goal_id`
- `run_id`
- `metric_scores`
- `weights`
- `overall_score`
- `pass_status`
- `warnings`
- `recommendations`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `artifact_ids`
- `metadata`

Indexes:

- unique `evaluation_report_id`
- `goal_id`
- `run_id`
- `overall_score`
- `pass_status`

Status values:

- `pass`
- `fail`
- `pass_with_warnings`

Relationships:

- Belongs to orchestration run and goal.

Embed vs reference:

- Separate document for reporting.

Repository owner:

- `EvaluationRepository`

### 10.19 OrchestrationRun

Purpose:

- Stores workflow run audit state.

Required fields:

- `_id`
- `run_id`
- `goal_id`
- `workflow_version`
- `status`
- `current_node`
- `completed_nodes`
- `failed_nodes`
- `node_events`
- `artifact_ids`
- `started_at`
- `created_at`
- `updated_at`
- `schema_version`

Optional fields:

- `completed_at`
- `errors`
- `warnings`
- `metadata`

Indexes:

- unique `run_id`
- `goal_id`
- `status`
- `started_at`

Status values:

- `created`
- `in_progress`
- `requires_input`
- `completed`
- `completed_with_warnings`
- `failed`

Relationships:

- References major artifacts generated during a workflow.

Embed vs reference:

- Embed node events for v1.
- Reference major artifacts by ID.

Repository owner:

- `OrchestrationRunRepository`


## 10a. ID Naming Conventions

All IDs should be opaque, URL-safe strings generated by the backend. Do not expose MongoDB `ObjectId` assumptions to frontend contracts.

Prefixes:
- `goal_`
- `run_`
- `assessment_`
- `answer_`
- `kmap_`
- `curriculum_`
- `week_`
- `topic_`
- `resource_`
- `attach_`
- `progress_`
- `quiz_`
- `question_`
- `attempt_`
- `adapt_`
- `critic_`
- `eval_`

## 10b. Idempotency Rules

To handle network retries safely, operations must be idempotent:
- Goal creation: Uses `client_request_id` to return existing goal on retry.
- Assessment answer submission: Safe to retry; replaces answer for same `question_id`.
- Curriculum generation: Idempotent per `knowledge_map_id` unless forced.
- Demo run start: Generates a new `run_id` but is idempotent for seeded data creation per run.
- Graph node re-execution: Graph nodes must be written to be safe to retry or must explicitly mark non-idempotent side effects. Repeated identical requests should not create duplicate resources or runs.

## 11. Repository Interfaces

Repository interfaces should be defined before MongoDB implementations. Fake repositories should use the same interfaces.

### 11.1 LearningGoalRepository

Responsibilities:

- Create and retrieve goals.
- Update goal status and metadata.

Methods:

```python
create(goal: LearningGoalCreate) -> LearningGoal
get_by_id(goal_id: str) -> LearningGoal | None
get_by_run_id(run_id: str) -> LearningGoal | None
update_status(goal_id: str, status: str) -> LearningGoal
update_profile(goal_id: str, learner_profile: LearnerProfile) -> LearningGoal
list_recent(limit: int = 20) -> list[LearningGoal]
```

### 11.2 AssessmentRepository

Responsibilities:

- Manage assessment sessions and answers.

Methods:

```python
create_session(data: AssessmentSessionCreate) -> AssessmentSession
get_session(session_id: str) -> AssessmentSession | None
get_session_by_goal_id(goal_id: str) -> AssessmentSession | None
update_session_status(session_id: str, status: str) -> AssessmentSession
update_confidence(session_id: str, confidence: float) -> AssessmentSession
append_answer(answer: AssessmentAnswerCreate) -> AssessmentAnswer
list_answers(session_id: str) -> list[AssessmentAnswer]
complete_session(session_id: str, termination_reason: str) -> AssessmentSession
```

### 11.3 KnowledgeMapRepository

Responsibilities:

- Save and retrieve knowledge maps.

Methods:

```python
create(data: KnowledgeMapCreate) -> KnowledgeMap
get_by_id(knowledge_map_id: str) -> KnowledgeMap | None
get_by_goal_id(goal_id: str) -> KnowledgeMap | None
mark_active(knowledge_map_id: str) -> KnowledgeMap
mark_superseded(knowledge_map_id: str) -> KnowledgeMap
```

### 11.4 CurriculumRepository

Responsibilities:

- Save curriculum drafts and active curricula.
- Update status and adaptations.

Methods:

```python
create(data: CurriculumCreate) -> Curriculum
get_by_id(curriculum_id: str) -> Curriculum | None
get_active_by_goal_id(goal_id: str) -> Curriculum | None
get_by_run_id(run_id: str) -> Curriculum | None
update_status(curriculum_id: str, status: str) -> Curriculum
replace_weeks(curriculum_id: str, weeks: list[CurriculumWeek]) -> Curriculum
append_critic_review_id(curriculum_id: str, critic_review_id: str) -> Curriculum
append_adaptation_event_id(curriculum_id: str, adaptation_event_id: str) -> Curriculum
```

### 11.5 ResourceRepository

Responsibilities:

- Store curated resource corpus.
- Search and rank resources.
- Save resource attachments.

Methods:

```python
upsert_resource(resource: ResourceCreate) -> Resource
get_resource(resource_id: str) -> Resource | None
list_resources(filters: ResourceFilter) -> list[Resource]
search_by_tags(tags: list[str], difficulty: str | None = None) -> list[Resource]
create_attachment(data: ResourceAttachmentCreate) -> ResourceAttachment
list_attachments_by_curriculum(curriculum_id: str) -> list[ResourceAttachment]
list_attachments_by_topic(curriculum_id: str, topic_id: str) -> list[ResourceAttachment]
mark_attachment_superseded(attachment_id: str) -> ResourceAttachment
```

### 11.6 ProgressRepository

Responsibilities:

- Initialize and update learner progress.

Methods:

```python
create(data: ProgressStateCreate) -> ProgressState
get_by_id(progress_state_id: str) -> ProgressState | None
get_by_goal_id(goal_id: str) -> ProgressState | None
update_topic_status(progress_state_id: str, topic_id: str, status: str) -> ProgressState
update_topic_score(progress_state_id: str, topic_id: str, score: float) -> ProgressState
append_stuck_event(progress_state_id: str, event: StuckEventCreate) -> ProgressState
update_weak_concepts(progress_state_id: str, weak_concepts: list[str]) -> ProgressState
update_current_topic(progress_state_id: str, topic_id: str) -> ProgressState
```

### 11.7 QuizRepository

Responsibilities:

- Store quizzes and attempts.

Methods:

```python
create_quiz(data: QuizCreate) -> Quiz
get_quiz(quiz_id: str) -> Quiz | None
get_active_by_goal_id(goal_id: str) -> Quiz | None
list_by_curriculum_id(curriculum_id: str) -> list[Quiz]
create_attempt(data: QuizAttemptCreate) -> QuizAttempt
get_attempt(quiz_attempt_id: str) -> QuizAttempt | None
list_attempts_by_quiz(quiz_id: str) -> list[QuizAttempt]
list_attempts_by_goal(goal_id: str) -> list[QuizAttempt]
update_quiz_status(quiz_id: str, status: str) -> Quiz
```

### 11.8 AdaptationRepository

Responsibilities:

- Store adaptation events.

Methods:

```python
create(data: AdaptationEventCreate) -> AdaptationEvent
get_by_id(adaptation_event_id: str) -> AdaptationEvent | None
list_by_goal_id(goal_id: str) -> list[AdaptationEvent]
list_by_curriculum_id(curriculum_id: str) -> list[AdaptationEvent]
update_status(adaptation_event_id: str, status: str) -> AdaptationEvent
```

### 11.9 CriticReviewRepository

Responsibilities:

- Store critic reviews and revision history.

Methods:

```python
create(data: CriticReviewCreate) -> CriticReview
get_by_id(critic_review_id: str) -> CriticReview | None
list_by_curriculum_id(curriculum_id: str) -> list[CriticReview]
list_by_run_id(run_id: str) -> list[CriticReview]
get_latest_by_curriculum_id(curriculum_id: str) -> CriticReview | None
```

### 11.10 EvaluationRepository

Responsibilities:

- Store evaluation reports.

Methods:

```python
create(data: EvaluationReportCreate) -> EvaluationReport
get_by_id(evaluation_report_id: str) -> EvaluationReport | None
get_by_run_id(run_id: str) -> EvaluationReport | None
list_by_goal_id(goal_id: str) -> list[EvaluationReport]
```

### 11.11 OrchestrationRunRepository

Responsibilities:

- Store run state and node events.

Methods:

```python
create(data: OrchestrationRunCreate) -> OrchestrationRun
get_by_id(run_id: str) -> OrchestrationRun | None
get_latest_by_goal_id(goal_id: str) -> OrchestrationRun | None
update_status(run_id: str, status: str) -> OrchestrationRun
update_current_node(run_id: str, node: str) -> OrchestrationRun
append_event(run_id: str, event: WorkflowNodeEvent) -> OrchestrationRun
append_error(run_id: str, error: WorkflowError) -> OrchestrationRun
append_warning(run_id: str, warning: WorkflowWarning) -> OrchestrationRun
set_artifact_id(run_id: str, artifact_name: str, artifact_id: str) -> OrchestrationRun
complete(run_id: str, status: str) -> OrchestrationRun
```

## 12. Service Layer Contracts

### 12.1 GoalService

Can:

- Validate and normalize goal text.
- Create a goal.
- Retrieve goal summary.
- Update goal status through repository.

Cannot:

- Generate curriculum directly.
- Call LLM directly except through orchestration-approved flows.
- Write to MongoDB outside repository.

### 12.2 AssessmentService

Can:

- Start assessment sessions.
- Request assessment questions from orchestration or agent.
- Save answers and scores.
- Finalize assessment.

Cannot:

- Persist knowledge maps directly unless delegated by a defined workflow method.
- Store prompt strings in database without clear metadata policy.

### 12.3 KnowledgeMapService

Can:

- Build knowledge map from assessment artifacts.
- Validate concept mastery output.
- Save and retrieve maps.

Cannot:

- Own assessment question selection.
- Mutate curriculum directly.

### 12.4 CurriculumService

Can:

- Generate curriculum through orchestration or agent.
- Validate curriculum structure.
- Save curriculum.
- Apply approved adaptation changes.

Cannot:

- Directly scrape resources.
- Update progress without ProgressService.

### 12.5 ResourceService

Can:

- Load curated corpus.
- Rank resources.
- Attach resources to topics.
- Retrieve attachments.

Cannot:

- Perform live web scraping in v1.
- Decide the whole curriculum.

### 12.6 ProgressService

Can:

- Initialize progress from curriculum.
- Update topic progress.
- Track stuck events.
- Store weak concept state.

Cannot:

- Generate adaptation plans directly.
- Change curriculum structure directly.

### 12.7 QuizService

Can:

- Generate quiz through quiz agent.
- Save quiz.
- Score attempts.
- Update weak concept outputs.

Cannot:

- Independently adapt curriculum.
- Store hidden answer keys in frontend responses.

### 12.8 AdaptationService

Can:

- Evaluate adaptation triggers.
- Request adapter output.
- Save adaptation events.
- Apply bounded changes through CurriculumService.

Cannot:

- Delete entire curriculum.
- Modify unrelated goals.

### 12.9 CriticService

Can:

- Run critic review.
- Save critic review.
- Determine pass/revise status using configured thresholds.

Cannot:

- Persist revised curriculum without CurriculumService.

### 12.10 EvaluationService

Can:

- Compute deterministic scores.
- Build evaluation report.
- Save report.

Cannot:

- Hide failed metrics.
- Replace actual artifact validation with narrative-only review.

### 12.11 OrchestrationService

Can:

- Start local demo workflow.
- Call LangGraph.
- Persist run state through OrchestrationRunRepository.
- Return workflow results.

Cannot:

- Bypass service-level persistence rules.
- Mix frontend display formatting into workflow state.

### 12.12 DashboardService

Can:

- Read persisted artifacts.
- Compose command center payload.
- Return learner-facing summaries.

Cannot:

- Mutate core workflow artifacts.
- Call LLMs.
- Generate hidden state.


## 12a. Error Handling And Observability

- **Trace Propagation:** Every log must include `request_id` and `run_id`.
- **Structured Logs:** Logs per node containing `node_start`, `node_success`, and `node_failed` events.
- **Conditional Tracing:** Explicitly log the reason for conditional branch decisions (e.g., "confidence 0.8 > threshold 0.75").
- **Retry Tracking:** Log retry counts.
- **Failure Categories:** Classify errors as `validation_error`, `llm_error`, `retrieval_error`, `persistence_error`, `user_input_error`, or `unknown_error`.
- **Safe Frontend Errors:** Never expose raw stack traces or LLM prompts to the frontend.
- **No Secret Logging:** Never log PII, `.env` vars, or API keys.

## 13. API Contract Plan

No-auth API endpoints should use local demo IDs and backend persistence. Request and response schemas should be defined before implementation.

### 13.1 Health And Readiness

```text
GET /api/v1/health
```

- Purpose: basic backend health.
- Request: none.
- Response: status, version, timestamp.
- Service used: health/core.
- Persistence effect: none.

```text
GET /api/v1/readiness
```

- Purpose: validate required local demo services are configured.
- Request: none.
- Response: readiness flags for database, corpus, LLM mode.
- Service used: health/core.
- Persistence effect: none.

### 13.2 Goal Creation

```text
POST /api/v1/goals
```

- Purpose: create learning goal.
- Request: goal text, optional learner profile, demo mode.
- Response: goal ID, status, normalized goal.
- Service used: GoalService.
- Persistence effect: creates LearningGoal.

```text
GET /api/v1/goals/{goalId}
```

- Purpose: retrieve goal.
- Request: goal ID.
- Response: LearningGoal response DTO.
- Service used: GoalService.
- Persistence effect: none.

### 13.3 Assessment

```text
POST /api/v1/goals/{goalId}/assessment/start
```

- Purpose: start diagnostic assessment.
- Request: optional learner profile updates.
- Response: assessment session ID, first question if generated synchronously.
- Service used: AssessmentService.
- Persistence effect: creates AssessmentSession.

```text
POST /api/v1/assessment/{sessionId}/answer
```

- Purpose: submit answer and receive next step.
- Request: question ID, answer payload.
- Response: score summary, continue flag, next question or finalization hint.
- Service used: AssessmentService.
- Persistence effect: creates AssessmentAnswer, updates AssessmentSession.

```text
POST /api/v1/assessment/{sessionId}/finalize
```

- Purpose: finalize assessment and build knowledge map.
- Request: optional force finalize flag.
- Response: assessment summary, knowledge map ID.
- Service used: AssessmentService and KnowledgeMapService.
- Persistence effect: completes AssessmentSession, creates KnowledgeMap.

### 13.4 Knowledge Map

```text
GET /api/v1/goals/{goalId}/knowledge-map
```

- Purpose: retrieve latest knowledge map.
- Request: goal ID.
- Response: KnowledgeMap DTO.
- Service used: KnowledgeMapService.
- Persistence effect: none.

### 13.5 Curriculum

```text
POST /api/v1/goals/{goalId}/curriculum/generate
```

- Purpose: generate curriculum.
- Request: duration weeks, hours per week, optional preferences.
- Response: curriculum ID, curriculum summary.
- Service used: CurriculumService.
- Persistence effect: creates Curriculum.

```text
GET /api/v1/curricula/{curriculumId}
```

- Purpose: retrieve curriculum.
- Request: curriculum ID.
- Response: Curriculum DTO.
- Service used: CurriculumService.
- Persistence effect: none.

### 13.6 Resources

```text
POST /api/v1/curricula/{curriculumId}/resources/attach
```

- Purpose: attach resources to curriculum topics.
- Request: optional max resources per topic.
- Response: attachment list and coverage summary.
- Service used: ResourceService.
- Persistence effect: creates ResourceAttachment documents.

```text
GET /api/v1/curricula/{curriculumId}/resources
```

- Purpose: retrieve attachments.
- Request: curriculum ID.
- Response: resources grouped by topic.
- Service used: ResourceService.
- Persistence effect: none.

### 13.7 Critic Review

```text
POST /api/v1/curricula/{curriculumId}/critic-review
```

- Purpose: run critic review.
- Request: optional rubric override for local experiments.
- Response: critic review ID, score, pass status.
- Service used: CriticService.
- Persistence effect: creates CriticReview.

### 13.8 Progress

```text
POST /api/v1/goals/{goalId}/progress/initialize
```

- Purpose: initialize progress from active curriculum.
- Request: curriculum ID.
- Response: progress state ID and current topic.
- Service used: ProgressService.
- Persistence effect: creates ProgressState.

```text
PATCH /api/v1/progress/{progressStateId}/topics/{topicId}
```

- Purpose: update topic status.
- Request: status, optional score, optional note.
- Response: updated ProgressState summary.
- Service used: ProgressService.
- Persistence effect: updates ProgressState.

```text
GET /api/v1/goals/{goalId}/progress
```

- Purpose: retrieve progress.
- Request: goal ID.
- Response: ProgressState DTO.
- Service used: ProgressService.
- Persistence effect: none.

### 13.9 Quiz

```text
POST /api/v1/goals/{goalId}/quiz/generate
```

- Purpose: generate quiz.
- Request: curriculum ID, target topic IDs, question count.
- Response: quiz ID and learner-safe quiz questions.
- Service used: QuizService.
- Persistence effect: creates Quiz.

```text
GET /api/v1/quizzes/{quizId}
```

- Purpose: retrieve learner-safe quiz.
- Request: quiz ID.
- Response: quiz without hidden answer key if learner-facing.
- Service used: QuizService.
- Persistence effect: none.

```text
POST /api/v1/quizzes/{quizId}/submit
```

- Purpose: submit quiz attempt.
- Request: answers.
- Response: score, weak concepts, adaptation recommendation flag.
- Service used: QuizService.
- Persistence effect: creates QuizAttempt, updates progress weak concepts.

```text
GET /api/v1/goals/{goalId}/quiz-attempts
```

- Purpose: retrieve quiz history.
- Request: goal ID.
- Response: attempt list.
- Service used: QuizService.
- Persistence effect: none.

### 13.10 Adaptation

```text
POST /api/v1/goals/{goalId}/adaptation/trigger
```

- Purpose: run adaptation if thresholds are met.
- Request: quiz attempt ID or stuck event details.
- Response: adaptation event ID, before/after summary, changes.
- Service used: AdaptationService.
- Persistence effect: creates AdaptationEvent and may update Curriculum.

```text
GET /api/v1/goals/{goalId}/adaptations
```

- Purpose: retrieve adaptation history.
- Request: goal ID.
- Response: list of adaptation events.
- Service used: AdaptationService.
- Persistence effect: none.

### 13.11 Evaluation

```text
POST /api/v1/goals/{goalId}/evaluation/run
```

- Purpose: evaluate full PathAI pipeline quality.
- Request: optional run ID.
- Response: evaluation report ID and scores.
- Service used: EvaluationService.
- Persistence effect: creates EvaluationReport.

```text
GET /api/v1/evaluations/{evaluationReportId}
```

- Purpose: retrieve evaluation report.
- Request: evaluation report ID.
- Response: EvaluationReport DTO.
- Service used: EvaluationService.
- Persistence effect: none.

### 13.12 Dashboard

```text
GET /api/v1/dashboard/{goalId}
```

- Purpose: retrieve learner command center payload.
- Request: goal ID.
- Response: full dashboard payload.
- Service used: DashboardService.
- Persistence effect: none.

### 13.13 Local Demo Run

```text
POST /api/v1/demo/run
```

- Purpose: starts a deterministic seeded demo run.
- Request: optional mode flags.
- Response: `run_id`, `goal_id`. Returns quickly, does NOT hold the HTTP request open.
- Service used: OrchestrationService.
- Behavior: It injects seeded assessment and quiz answers. It does not pretend to be normal interactive mode. Stores output under a normal `OrchestrationRun` labeled as `demo_mode`.
- Persistence effect: creates complete demo artifact chain.


```text
POST /api/v1/demo/run
```

- Purpose: execute deterministic canonical no-auth demo path.
- Request: optional mode flags.
- Response: run ID, goal ID, dashboard payload.
- Service used: OrchestrationService.
- Persistence effect: creates complete demo artifact chain.


### 13.14 Orchestration Polling Endpoints

Since LLM workflows are long-running, POST requests should not hold HTTP connections open. The frontend must poll for status.

```text
POST /api/v1/orchestration/runs
```
- Purpose: Queue a new workflow run.

```text
GET /api/v1/orchestration/runs/{run_id}
```
- Purpose: Get full run details.

```text
GET /api/v1/orchestration/runs/{run_id}/status
```
- Purpose: Lightweight polling endpoint for run status.
- Response: Status enum (`queued`, `running`, `waiting_for_user`, `completed`, `failed`, `cancelled`), current node.
- Recommendation: Poll every 2-3 seconds. Frontend should show appropriate loading/error states.

```text
GET /api/v1/orchestration/runs/{run_id}/events
```
- Purpose: Retrieve node execution events for progress visualization.

```text
POST /api/v1/orchestration/runs/{run_id}/cancel
```
- Purpose: Cancel a running workflow. (May be explicitly postponed for v1).

### 13.15 API DTO Details For Critical Endpoints

**POST /api/v1/goals**
- Request: `{ "goal_text": string, "learner_profile": object, "demo_mode": boolean }`
- Response: `{ "goal_id": string, "normalized_goal_text": string, "status": string }`

**POST /api/v1/assessments/{session_id}/answers**
- Request: `{ "question_id": string, "answer_text": string, "selected_options": list[str] }`
- Response: `{ "score": float, "confidence": float, "next_question": object | null, "is_complete": boolean }`

**POST /api/v1/assessments/{session_id}/finalize**
- Request: `{ "force": boolean }`
- Response: `{ "knowledge_map_id": string, "summary": string }`

**POST /api/v1/curricula/generate**
- Request: `{ "goal_id": string, "duration_weeks": int }`
- Response: `{ "curriculum_id": string, "status": string }`

**POST /api/v1/quizzes/{quiz_id}/submit**
- Request: `{ "answers": list[object] }`
- Response: `{ "score": float, "weak_concepts": list[str], "adaptation_recommended": boolean }`

**GET /api/v1/dashboard/{run_id}**
- Response: `DashboardPayload` (see section 18.5).

## 14. RAG Corpus Strategy

### 14.1 V1 Strategy

PathAI v1 should use a curated seed corpus. This is enough to make the RAG plan meaningful while avoiding live web scraping complexity and unstable external dependencies.

Recommended seed size:

- Minimum: 25 resources.
- Better target: 40 to 60 resources.
- Per major concept: at least 2 resources.
- Per weak canonical concept: at least 3 resources.

Topic coverage:

- RAG fundamentals.
- embeddings.
- chunking.
- vector databases.
- metadata filtering.
- retrieval ranking.
- reranking.
- prompt augmentation.
- hallucination reduction.
- RAG evaluation.
- FastAPI integration.
- project architecture.

Allowed resource types:

- documentation.
- tutorial.
- paper.
- article.
- video.
- code example.
- exercise.
- checklist.

Resource metadata schema:

```python
class ResourceSeedItem(BaseModel):
    resource_id: str
    title: str
    resource_type: str
    source_name: str
    url: str
    summary: str
    topic_tags: list[str]
    concept_ids: list[str]
    difficulty: Literal["beginner", "intermediate", "advanced"]
    estimated_minutes: int
    quality_score: float
    freshness_score: float | None
    license_note: str
    language: str = "en"
```

### 14.2 V1 Ranking Formula

V1 ranking should be deterministic and explainable.

Draft formula:

```text
tag_match_score = matched_topic_tags / requested_topic_tags
concept_match_score = matched_concepts / requested_concepts
difficulty_score = 1.0 if exact match, 0.75 if adjacent difficulty, 0.4 otherwise
quality_score = curated quality score
time_fit_score = 1.0 if estimated_minutes <= topic_budget, else max(0.4, topic_budget / estimated_minutes)

final_relevance_score =
    0.35 * concept_match_score +
    0.25 * tag_match_score +
    0.15 * difficulty_score +
    0.15 * quality_score +
    0.10 * time_fit_score
```

### 14.3 Embeddings Introduction

Embeddings should be introduced only after:

- seed corpus works.
- deterministic ranking tests pass.
- resources are attached successfully in the local demo.
- baseline quality is measurable.

Embedding-enhanced retrieval can add semantic similarity:

```text
final_score_v2 =
    0.45 * semantic_similarity +
    0.25 * concept_match_score +
    0.10 * difficulty_score +
    0.10 * quality_score +
    0.10 * diversity_adjustment
```

### 14.4 Why Live Web Scraping Is Postponed

Live web scraping is postponed because it introduces:

- source instability.
- network dependency.
- content quality uncertainty.
- licensing and attribution concerns.
- scraping policy concerns.
- test nondeterminism.
- demo instability.

The curated corpus is academically stronger for v1 because it allows quality-controlled retrieval and reproducible evaluation.

### 14.5 Resource Quality Scoring

Quality score should consider:

- authority of source.
- clarity.
- relevance to target concept.
- practical usefulness.
- freshness where applicable.
- level fit for student.
- availability and stability.

Draft manual scoring:

```text
0.90 - 1.00: excellent, authoritative, directly useful
0.75 - 0.89: strong, useful, minor limitations
0.60 - 0.74: acceptable, supplemental
below 0.60: do not include in seed corpus unless clearly justified
```

### 14.6 Resource Diversity

Diversity should be measured by resource type distribution and source distribution.

Draft diversity score:

```text
type_diversity = unique_resource_types_attached / max_expected_types
source_diversity = unique_sources_attached / total_resources_attached
diversity_score = 0.6 * type_diversity + 0.4 * source_diversity
```


### 14.7 Seed Corpus Acceptance Standard

The seed corpus must meet these minimum standards before the Resource Agent is implemented:
- **Size:** 40 to 60 resources specifically tailored for the canonical RAG demo goal.
- **Types required:** article, docs, video, exercise, paper, code/lab.
- **Fields required:** title, url/reference, source_name, source_type, topic_tags, concept_tags, difficulty, estimated_minutes, trust_score, quality_score, summary.
- **Diversity:** Multiple resource types per topic.

### 14.8 Clarification: RAG v1 vs v2

- **V1** uses a curated corpus with metadata/tag/difficulty/quality ranking.
- Embeddings and vector search are strictly **optional V2 enhancements** if time allows.
- Do not overclaim V1 as "open-web RAG". Academically, refer to it as "retrieval-augmented resource recommendation over a curated corpus".


## 15. Evaluation Rubric

All metrics use a 0.0 to 1.0 scoring range.
Pass threshold: >= 0.80. Pass with warnings: 0.70 to 0.79. Fail: < 0.70.
Deterministic metrics strictly use database fields.

### 15.1 Metric Definitions

#### Quiz Alignment
Measures whether quiz questions map to curriculum topics and *specifically* weak concepts from the knowledge map.
*Rule:* Quiz alignment fails or is heavily penalized if it only tests generic unrelated content instead of targeted weak areas.
```text
quiz_alignment = 
    0.6 * weak_concept_coverage + 
    0.4 * active_topic_alignment
```
#### Curriculum Coverage

Measures whether curriculum topics cover required concepts from the knowledge map and goal.

```text
coverage_score = covered_required_concepts / total_required_concepts
```

#### Difficulty Alignment

Measures whether curriculum difficulty matches learner profile and mastery.

```text
difficulty_alignment =
    aligned_topic_count / total_topic_count
```

A topic is aligned if its difficulty is appropriate for concept mastery:

- mastery below 0.35: beginner or scaffolded intermediate.
- mastery 0.35 to 0.70: intermediate.
- mastery above 0.70: intermediate or advanced extension.

#### Pacing Balance

Measures whether weekly workload is balanced.

```text
average_hours = total_estimated_hours / duration_weeks
max_deviation = max(abs(week_hours - average_hours)) / average_hours
pacing_score = max(0.0, 1.0 - max_deviation)
```

#### Resource Relevance

Measures average relevance of attached resources.

```text
resource_relevance = average(attachment.relevance_score)
```

#### Resource Diversity

Measures resource type and source diversity.

```text
resource_diversity =
    0.6 * normalized_type_diversity +
    0.4 * normalized_source_diversity
```

#### Quiz Alignment

Measures whether quiz questions map to curriculum topics and weak concepts.

```text
quiz_alignment =
    0.5 * concept_alignment +
    0.3 * topic_alignment +
    0.2 * difficulty_alignment
```

#### Critic Coherence

Measures whether critic scores are internally consistent and recommendations match issues.

```text
critic_coherence =
    0.4 * dimension_score_completeness +
    0.3 * issue_recommendation_match +
    0.3 * score_reasonableness
```

#### Adaptation Usefulness

Measured only when adaptation occurs.

```text
adaptation_usefulness =
    0.4 * weak_concept_targeting +
    0.3 * change_specificity +
    0.2 * workload_reasonableness +
    0.1 * before_after_clarity
```

If no adaptation is needed, this metric can be marked `not_applicable` and excluded from weighted total.

### 15.2 Draft Weights

```text
curriculum_coverage: 0.18
difficulty_alignment: 0.12
pacing_balance: 0.10
resource_relevance: 0.14
resource_diversity: 0.08
quiz_alignment: 0.12
critic_coherence: 0.10
adaptation_usefulness: 0.10
workflow_completeness: 0.06
```

If adaptation is not applicable, redistribute its 0.10 weight proportionally across the remaining metrics.

### 15.3 Overall PathAI Score

```text
overall_pathai_score = sum(metric_score * metric_weight)
```

Pass/fail thresholds:

```text
overall >= 0.80: pass
0.70 <= overall < 0.80: pass_with_warnings
overall < 0.70: fail
```

Blocking failure conditions:

- missing curriculum.
- missing knowledge map.
- no resources attached to any topic.
- quiz has no concept mapping.
- malformed agent output accepted into persistence.

## 16. Adapter/Replanning Rules

### 16.1 Exact Triggers

Adaptation should run when at least one trigger is true:

```text
quiz_score < QUIZ_ADAPTATION_THRESHOLD
same_topic_stuck_count >= STUCK_EVENT_THRESHOLD
critic_score < CRITIC_PASS_SCORE after allowed revision loop
```

Draft constants:

```text
QUIZ_ADAPTATION_THRESHOLD = 0.65
STUCK_EVENT_THRESHOLD = 2
CRITIC_PASS_SCORE = 0.80
```


### 16.1 Exact Triggers
- `quiz_score < 0.65`
- `same_topic_stuck_count >= 2`
- `critic_score < 0.80` after max revision loops

### 16.2 Constraints
- Max 3 adaptations per workflow run to prevent infinite loops.
- User-visible explanation must be generated and presented on the dashboard.
- Effectiveness is evaluated by comparing the subsequent quiz score on the targeted concept.

### 16.2 Allowed Adaptation Actions

Allowed:

- Insert a remedial topic.
- Add practice exercise.
- Reorder nearby topics.
- Reduce difficulty for one topic.
- Add additional resource attachment.
- Add a review checkpoint quiz.
- Split an overloaded topic into smaller steps.
- Defer an advanced topic.

### 16.3 Forbidden Adaptation Actions

Forbidden:

- Delete the whole curriculum.
- Change the user's original learning goal.
- Remove all advanced material permanently.
- Create unrelated topics.
- Modify other goals.
- Hide low quiz performance.
- Rewrite history of prior attempts.

### 16.4 Before/After Output

Every adaptation must produce:

- trigger reason.
- before summary.
- after summary.
- exact changes.
- affected concept IDs.
- affected topic IDs.
- expected benefit.

### 16.5 Storage

Adaptation is stored as:

- `AdaptationEvent` document.
- optional updated `Curriculum` status or new curriculum revision.
- progress state update showing weak concepts and next recommended topic.

### 16.6 Dashboard Display

Dashboard should show:

- adaptation trigger reason.
- weak concepts that caused replanning.
- what changed.
- next recommended action.
- whether adaptation was applied or only proposed.


### 16.7 Curriculum Versioning and Progress Synchronization

**Versioning:**
- Curricula use explicit versioning: `curriculum.version`, `curriculum.parent_curriculum_id`, `curriculum.revision_reason`.
- The Goal and Progress documents track `active_curriculum_id`.
- Critic revision (during generation) creates a new version before it's shown to the user. Adapter replanning (mid-flight) creates a new version from the active one.
- The Dashboard always shows the `active_curriculum_id`.

**Progress Synchronization After Adaptation:**
- Adaptation creates a *new* curriculum revision, it does not destructively mutate the old one.
- `ProgressState` must diff old vs new topics.
- Preserve progress/scores for unchanged topics.
- Mark removed topics as `superseded` or `archived`.
- Initialize progress for newly inserted topics.
- Link `AdaptationEvent` to `before_curriculum_id` and `after_curriculum_id`.

## 17. LLM Client Strategy

### 17.1 Interface Responsibilities

The LLM client abstraction should provide:

- provider-independent completion method.
- structured-output request method.
- timeout handling.
- retry metadata.
- model name and provider metadata.
- token usage where available.
- safe error object.

Draft interface:

```python
class LLMClient(Protocol):
    async def generate_text(self, request: LLMTextRequest) -> LLMTextResponse:
        ...

    async def generate_structured(
        self,
        request: LLMStructuredRequest,
        output_schema: type[BaseModel],
    ) -> LLMStructuredResponse:
        ...
```

### 17.2 Mock LLM

Mock LLM must:

- return deterministic outputs.
- support all agent contracts.
- run without network calls.
- be default for tests.
- support intentional malformed-output fixtures for parser tests.

### 17.3 University-Hosted LLM

Real LLM client must:

- use configuration from settings.
- avoid hard-coded secrets.
- support structured output parsing.
- expose provider/model metadata.
- fail safely if unavailable.

### 17.4 Timeout Policy

Draft policy:

```text
LLM_TIMEOUT_SECONDS = 45
```

If timeout occurs:

1. retry once for transient errors.
2. retry second time only if configured by `MAX_NODE_RETRIES`.
3. in demo mode, use deterministic fallback output.
4. outside demo mode, return structured failure.

### 17.5 Retry Policy

Retry only:

- timeouts.
- transient connection errors.
- malformed structured output that can be repaired.

Do not retry:

- invalid input.
- missing required settings.
- schema version mismatch.

### 17.6 Structured Output Parsing Policy

Policy:

- Parse all agent outputs into Pydantic schemas.
- Reject extra dangerous or unknown root structures unless explicitly allowed.
- Store validation errors in workflow state.
- Use repair prompt once for malformed output.
- Fall back to deterministic mock only in demo/test mode.

### 17.7 Test Isolation Rules

Default tests must not call real LLMs.

Test types:

- schema tests: no LLM.
- service tests: mock agents or mock LLM.
- orchestration tests: mock LLM.
- integration tests: fake repositories unless Mongo integration is explicitly marked.
- live LLM smoke tests: optional, skipped by default.


### 17.8 LLM Client Contract Policy

- One unified `LLMClient` interface.
- Mock client for default tests (no real LLM calls).
- Real university-hosted client.
- Strict timeout and retry limits (e.g., 2 retries).
- Built-in structured output parsing using Pydantic.
- Single schema repair attempt if parsing fails.
- No silent fallback to fake success in normal interactive mode; it must fail gracefully.
- Deterministic fallback allowed *only* in explicit demo mode or tests, and must be clearly labeled.

## 18. Frontend Information Architecture

The frontend must be learner-facing, not developer-console-facing. It should display intelligence and progress without exposing raw orchestration noise.

### 18.1 Planned Routes

#### `/`

- Purpose: entry point.
- Endpoints: optional health or demo status.
- States: ready, backend unavailable, loading.

#### `/learn/new`

- Purpose: create new learning goal.
- Endpoints: `POST /api/v1/goals`.
- States: empty form, submitting, validation error, created.

#### `/assessment/[sessionId]`

- Purpose: answer diagnostic questions.
- Endpoints: `POST /assessment/{sessionId}/answer`, `POST /assessment/{sessionId}/finalize`.
- States: loading question, answering, scoring, completed, error.

#### `/knowledge-map/[goalId]`

- Purpose: show concept mastery map.
- Endpoints: `GET /goals/{goalId}/knowledge-map`.
- States: loading, empty, ready, error.

#### `/curriculum/[curriculumId]`

- Purpose: show week-by-week curriculum.
- Endpoints: `GET /curricula/{curriculumId}`.
- States: loading, generated, empty, error.

#### `/resources/[curriculumId]`

- Purpose: show resources grouped by topic.
- Endpoints: `GET /curricula/{curriculumId}/resources`.
- States: loading, attached, coverage warning, error.

#### `/quiz/[quizId]`

- Purpose: take quiz and view result.
- Endpoints: `GET /quizzes/{quizId}`, `POST /quizzes/{quizId}/submit`.
- States: loading, taking quiz, submitting, result, adaptation recommended, error.

#### `/progress/[goalId]`

- Purpose: show progress details.
- Endpoints: `GET /goals/{goalId}/progress`, `PATCH /progress/{progressStateId}/topics/{topicId}`.
- States: loading, ready, empty, error.

#### `/adaptation/[goalId]`

- Purpose: show adaptation events and changes.
- Endpoints: `GET /goals/{goalId}/adaptations`, `POST /goals/{goalId}/adaptation/trigger`.
- States: none needed, eligible, applied, error.

#### `/command-center`

- Purpose: main learner dashboard.
- Endpoints: `GET /dashboard/{goalId}`.
- States: no active goal, loading, ready, partial data, error.

#### `/demo`

- Purpose: run canonical no-auth demo.
- Endpoints: `POST /api/v1/demo/run`.
- States: ready to run, running, completed, failed.

### 18.2 Local No-Auth ID Handling

For the local no-auth demo:

- store last active `goalId` and `runId` in local storage.
- backend remains the source of truth.
- route params should use backend IDs.
- local storage should only improve navigation continuity.

### 18.3 Dashboard Sections

Command center sections:

- Active learning goal.
- Current status and next action.
- Knowledge map summary.
- Curriculum timeline.
- Resource recommendations.
- Quiz result and weak concepts.
- Progress overview.
- Adaptation summary.
- Critic review score.
- PathAI quality score.

### 18.4 Loading, Empty, And Error States

Every route should define:

- loading state.
- empty state.
- recoverable error state.
- failed workflow state.
- partial data state if upstream artifact exists but downstream artifact is not generated yet.


### 18.5 Dashboard Payload Schema

The Dashboard payload is a read-model specifically composed by the `DashboardService` for UI convenience. It does NOT replace canonical stored documents.

```json
{
  "run_summary": { "run_id": "...", "status": "running", "mode": "demo" },
  "goal_summary": { "goal_id": "...", "text": "..." },
  "knowledge_map_summary": { "strong_concepts": [], "weak_concepts": [] },
  "curriculum_summary": { "active_curriculum_id": "...", "weeks": [] },
  "progress_summary": { "completion_percentage": 45, "current_topic": "..." },
  "quiz_summary": { "latest_score": 0.85 },
  "resources_summary": { "total_attached": 12 },
  "adaptation_summary": { "recent_events": [] },
  "evaluation_summary": { "overall_score": 0.92, "pass_status": "pass" },
  "ui_flags": { "show_adaptation_alert": false, "requires_user_input": false }
}
```

### 18.6 Frontend State And Polling Behavior

- **Interactive Routes:** `/learn/new`, `/assessment/[sessionId]`, `/quiz/[quizId]` require manual user input.
- **Read-Only / Demo Routes:** `/command-center`, `/curriculum/[curriculumId]` visualize state.
- **Polling:** The frontend polls `GET /api/v1/orchestration/runs/{run_id}/status` every 2s for active workflows.
- **Loading States:** UI must gracefully show skeleton loaders. No debug-heavy JSON dumps in normal views.
- **Missing IDs/Offline:** Handle 404s cleanly. Local storage of `run_id` provides session continuity, but backend is the source of truth.

## 19. UI Product Direction

PathAI should feel like a premium learner command center, not a debug dashboard.

Direction:

- light, modern, and polished.
- cinematic but usable.
- calm, structured information density.
- no unnecessary developer logs in learner UI.
- show intelligence through clear recommendations and evidence.
- use the official UX/design assets in the `Design` folder as visual direction if present.
- dashboard is the main command center.
- avoid generic AI-generated-looking visuals.
- prioritize legibility and state clarity.
- show the system's reasoning in learner-friendly summaries, not raw prompts.

Screens should answer:

- What am I learning?
- What do I already know?
- What should I do next?
- Why did the system recommend this?
- How am I progressing?
- What changed after adaptation?

## 20. Testing Strategy

### 20.1 Schema Tests

Purpose:

- Validate Pydantic schemas.
- Reject malformed agent output.
- Verify field constraints.

Examples:

- curriculum must contain weeks.
- quiz questions must map to concept IDs.
- scores must be between 0.0 and 1.0.

### 20.2 Repository Tests With Fake Repositories

Purpose:

- Validate repository contracts before MongoDB.
- Support service tests without database dependency.

Examples:

- create and retrieve LearningGoal.
- append AssessmentAnswer.
- save and retrieve Curriculum.

### 20.3 Service Tests

Purpose:

- Validate business rules.
- Confirm services own persistence decisions.

Examples:

- assessment exits after min questions and confidence target.
- critic loop respects max revision attempts.
- adaptation triggers below quiz threshold.

### 20.4 Agent Tests With Mock LLM Outputs

Purpose:

- Verify parser and validation behavior.
- Avoid live network calls.

Examples:

- valid mock curriculum parses.
- malformed quiz output is rejected.
- repair path is attempted once.

### 20.5 LangGraph Orchestration Tests

Purpose:

- Verify node order, transitions, loop caps, and failure handling.

Examples:

- canonical demo reaches dashboard payload.
- assessment loop stops at confidence target.
- critic loop stops at pass score.
- adaptation runs for low quiz score.

### 20.6 No-Auth E2E Test

Purpose:

- Validate local happy path through backend API and frontend screens.

Minimum path:

1. create goal.
2. start assessment.
3. answer questions.
4. finalize knowledge map.
5. generate curriculum.
6. attach resources.
7. run critic.
8. initialize progress.
9. generate quiz.
10. submit quiz.
11. trigger adaptation.
12. view dashboard.

### 20.7 Frontend Checks Later

After dependencies and frontend foundation exist:

- lint.
- type check.
- build.
- route rendering checks.
- API client contract checks.

### 20.8 Manual Demo Checklist

Manual validation should confirm:

- demo run completes.
- all major IDs are generated.
- dashboard displays all major artifacts.
- quiz score can trigger adaptation.
- no auth is required.
- no secrets are exposed.
- no live LLM is required in default demo mode.


## 20a. Demo Seed Dataset Requirements

The canonical demo requires a robust seed dataset to guarantee deterministic E2E runs:
- **Demo Goal:** "Learn RAG systems for an AI engineering graduation project"
- **Learner Profile:** Intermediate Python, beginner RAG.
- **Seeded Assessment:** Pre-defined questions and answers ensuring specific concepts are flagged as weak (e.g., "retrieval evaluation").
- **Expected Knowledge Map:** Hardcoded classification matching the seeded assessment.
- **Expected Curriculum:** 4-week structured JSON.
- **Seed Resources:** Curated corpus mapping to the curriculum topics.
- **Seeded Quiz:** Pre-defined low-scoring attempt to force adaptation.
- **Expected Adaptation:** Hardcoded insertion of a remedial topic.
- **Expected Evaluation Report:** Pass score > 0.80.

## 21. Scope Control

The following remain out of scope until after the no-auth demo works:

- authentication.
- JWT.
- login/register.
- password hashing.
- sessions.
- Docker.
- deployment.
- CI/CD.
- production hosting.
- live web scraping.
- production observability.
- multi-user accounts.
- admin panels.
- advanced vector infrastructure.
- fine-tuning.
- streaming LLM responses.
- payment or billing.
- role-based access control.
- complex collaborative learning features.
- mobile app.
- LMS integrations.

## 22. Implementation Roadmap

Each phase should produce a recap file in `reports/phases`.

> **Roadmap numbering amendment (post Rebuild-8):** Execution diverged from the phase numbers below starting at Rebuild-5 and continued on an independently-numbered backend-first track through Rebuild-13. The phase content below (`Rebuild-0B` through `Rebuild-14`) is preserved as original design-time reference material; it does not reflect actual execution order or status from Rebuild-5 onward. The authoritative, currently adopted execution roadmap is `reports/phases/Phase_Roadmap_Alignment_Note_Post_Rebuild8.md`. In summary: the MongoDB persistence and frontend work described below under Rebuild-9 through Rebuild-12 have not yet been executed under those numbers — they are rescheduled to Rebuild-17 and Rebuild-19/20 respectively, with full E2E validation and final polish now Rebuild-18 and Rebuild-21. Consult that note, not the phase numbers below, for actual project status.

### Rebuild-0B: Architecture Contracts And Roadmap

Goal:

- Create implementation-ready contracts and roadmap.

Files/modules affected:

- `docs/architecture/PathAI_Global_Architecture_And_Implementation_Blueprint.md`
- `reports/phases/Rebuild_0B_Architecture_Contracts_And_Roadmap_Result.md`

Deliverables:

- Architecture contract document.
- Phase result document.

Validation commands:

- safe file existence checks.
- section presence checks.

Done criteria:

- Required sections exist.
- No runtime code implemented.
- `.env` not   modified.

Recap file:

- `reports/phases/Rebuild_0B_Architecture_Contracts_And_Roadmap_Result.md`

### Rebuild-1: Backend Project Foundation, Tooling, And LLM Spike

Goal:
- Initialize backend tooling and perform an early LLM structured-output spike.
- Test whether the university LLM can return valid JSON for KnowledgeMap, Curriculum, and Quiz schemas. If not, simplify schemas before Phase 2.

Goal:

- Initialize backend tooling without implementing product runtime behavior.

Files/modules affected:

- backend packaging files.
- backend app entrypoint.
- test config.
- lint/type config if selected.

Deliverables:

- FastAPI app skeleton.
- settings skeleton.
- health endpoint.
- test runner configured.

Validation commands:

- backend unit test command.
- import check.
- health endpoint smoke check if server is run.

Done criteria:

- backend starts locally.
- no business workflow implemented.
- settings do not expose secrets.

Recap file:

- `reports/phases/Rebuild_1_Backend_Foundation_Result.md`

### Rebuild-2: Core Schemas And Contracts

*(Merged with Mock LLM fixtures from old phase 5 to validate schemas immediately)*

Goal:

- Implement Pydantic schemas for API, agents, database models, and workflow state.

Files/modules affected:

- `backend/app/schemas`
- `backend/app/models`
- `backend/app/orchestration`

Deliverables:

- schema definitions.
- constants.
- validation tests.

Validation commands:

- schema unit tests.

Done criteria:

- all major contracts compile.
- malformed sample outputs fail validation.

Recap file:

- `reports/phases/Rebuild_2_Core_Schemas_And_Contracts_Result.md`

### Rebuild-4: Fake Repositories And Service Skeleton

Goal:

- Build repository interfaces, fake repositories, and service skeletons.

Files/modules affected:

- `backend/app/repositories`
- `backend/app/services`
- `backend/app/tests`

Deliverables:

- fake repositories.
- service methods.
- service tests.

Validation commands:

- backend service test command.

Done criteria:

- services can create and retrieve major artifacts using fake repos.

Recap file:

- `reports/phases/Rebuild_3_Fake_Repositories_And_Services_Result.md`

### Rebuild-9: MongoDB Persistence Swap-in

Goal:

- Add MongoDB connection and Mongo-backed repositories behind existing interfaces.

Files/modules affected:

- `backend/app/db`
- `backend/app/repositories`
- `backend/app/core`

Deliverables:

- Mongo connection.
- index initialization.
- Mongo repository implementations.

Validation commands:

- repository integration tests marked separately.

Done criteria:

- fake repos still work.
- Mongo repos satisfy same tests where configured.
- `.env` remains private.

Recap file:

- `reports/phases/Rebuild_4_MongoDB_Persistence_Foundation_Result.md`

### Rebuild-3: Mock LLM And Deterministic Agent Fixtures

Goal:

- Implement mock LLM and deterministic agent fixtures.

Files/modules affected:

- `backend/app/agents`
- `backend/app/core`
- `backend/app/tests`

Deliverables:

- LLM interface.
- mock LLM.
- deterministic canonical outputs.

Validation commands:

- agent contract tests.

Done criteria:

- all agents can return valid structured outputs without network calls.

Recap file:

- `reports/phases/Rebuild_5_Mock_LLM_And_Deterministic_Agents_Result.md`

### Rebuild-5: LangGraph Straight-Line Orchestration With Lightweight State

Goal:

- Implement first graph skeleton for happy path.

Files/modules affected:

- `backend/app/orchestration`
- `backend/app/services/orchestration`

Deliverables:

- graph nodes.
- graph transitions.
- workflow state tests.

Validation commands:

- orchestration tests with mock agents and fake repos.

Done criteria:

- canonical graph completes with deterministic artifacts.

Recap file:

- `reports/phases/Rebuild_6_LangGraph_Straight_Line_Orchestration_Result.md`

### Rebuild-6: Assessment And Knowledge Map

Goal:

- Implement assessment loop and knowledge map generation.

Files/modules affected:

- assessment agent/service/repository.
- knowledge map agent/service/repository.

Deliverables:

- assessment endpoints.
- knowledge map endpoints.
- tests for loop exit.

Validation commands:

- assessment and knowledge map tests.

Done criteria:

- assessment exits correctly.
- knowledge map persists.

Recap file:

- `reports/phases/Rebuild_7_Assessment_And_Knowledge_Map_Result.md`

### Rebuild-7: Curriculum, Resources, And Critic

Goal:

- Implement curriculum generation and persistence.

Files/modules affected:

- curriculum agent/service/repository.

Deliverables:

- curriculum endpoint.
- curriculum validation.
- deterministic demo curriculum.

Validation commands:

- curriculum service and schema tests.

Done criteria:

- curriculum aligns to knowledge map and goal.

Recap file:

- `reports/phases/Rebuild_8_Curriculum_Generation_Result.md`

*(Merged into Rebuild-7)*

Goal:

- Implement curated corpus and metadata ranking.

Files/modules affected:

- `data`
- `backend/app/rag`
- resource service/repository.

Deliverables:

- seed corpus.
- ranking formula.
- resource attachment endpoint.

Validation commands:

- RAG ranking tests.
- resource attachment tests.

Done criteria:

- each canonical curriculum topic receives relevant resources or explicit warning.

Recap file:

- `reports/phases/Rebuild_9_RAG_Resource_Attachment_Result.md`

*(Critic merged into Rebuild-7, Evaluation into Rebuild-8)*

Goal:

- Implement critic review and deterministic evaluation report.

Files/modules affected:

- critic agent/service/repository.
- evaluation module/service/repository.

Deliverables:

- critic endpoint.
- evaluation endpoint.
- scoring formulas.

Validation commands:

- critic and evaluation tests.

Done criteria:

- curriculum receives score.
- evaluation report persists with weighted total.

Recap file:

- `reports/phases/Rebuild_10_Critic_And_Evaluation_Result.md`

### Rebuild-8: Progress, Quiz, And Adaptation

Goal:

- Implement progress state, quiz generation, and quiz scoring.

Files/modules affected:

- progress service/repository.
- quiz agent/service/repository.

Deliverables:

- progress endpoints.
- quiz endpoints.
- scoring tests.

Validation commands:

- progress and quiz tests.

Done criteria:

- quiz attempt updates weak concepts and progress.

Recap file:

- `reports/phases/Rebuild_11_Progress_And_Quiz_Result.md`

*(Merged into Rebuild-8)*

Goal:

- Implement adaptation trigger and bounded curriculum changes.

Files/modules affected:

- adapter agent/service/repository.
- curriculum service.
- progress service.

Deliverables:

- adaptation endpoint.
- before/after event.
- threshold tests.

Validation commands:

- adaptation service tests.

Done criteria:

- low quiz score triggers stored adaptation event and dashboard-visible changes.

Recap file:

- `reports/phases/Rebuild_12_Adapter_Replanning_Result.md`

### Rebuild-10: Frontend Foundation And Design System

Goal:

- Set up frontend foundation and design system.

Files/modules affected:

- `frontend/app`
- `frontend/components`
- `frontend/styles`
- `frontend/lib`

Deliverables:

- layout.
- global styles.
- API client.
- base components.

Validation commands:

- frontend lint/type/build once dependencies exist.

Done criteria:

- frontend renders base shell and can call health endpoint.

Recap file:

- `reports/phases/Rebuild_13_Frontend_Foundation_And_Design_System_Result.md`

### Rebuild-11: Frontend No-Auth Workflow Screens

Goal:

- Build route screens for the no-auth workflow.

Files/modules affected:

- frontend app routes.
- feature components.
- API client.

Deliverables:

- goal creation screen.
- assessment screen.
- knowledge map screen.
- curriculum screen.
- resource screen.
- quiz screen.
- adaptation screen.

Validation commands:

- frontend build/lint/type checks.
- manual workflow smoke test.

Done criteria:

- user can navigate through the happy path screens.

Recap file:

- `reports/phases/Rebuild_14_Frontend_No_Auth_Workflow_Screens_Result.md`

### Rebuild-12: Dashboard Command Center

Goal:

- Build command center dashboard.

Files/modules affected:

- `/command-center`
- dashboard components.
- DashboardService API client.

Deliverables:

- complete dashboard payload rendering.
- partial state handling.
- adaptation and evaluation sections.

Validation commands:

- frontend checks.
- manual dashboard validation.

Done criteria:

- dashboard displays all major persisted artifacts.

Recap file:

- `reports/phases/Rebuild_15_Dashboard_Command_Center_Result.md`

### Rebuild-13: Full No-Auth E2E Validation

Goal:

- Validate end-to-end no-auth demo.

Files/modules affected:

- backend tests.
- frontend tests.
- E2E scripts.
- reports.

Deliverables:

- local E2E test.
- manual demo script.
- bug fixes.

Validation commands:

- backend tests.
- frontend checks.
- E2E test command.

Done criteria:

- canonical demo completes repeatedly without manual database fixes.

Recap file:

- `reports/phases/Rebuild_16_Full_Local_E2E_Validation_Result.md`

### Rebuild-14: Final Demo Polish And Academic Evidence

Goal:

- Prepare final project evidence and presentation material.

Files/modules affected:

- docs.
- reports.
- screenshots.
- evaluation outputs.

Deliverables:

- architecture diagram.
- demo screenshots.
- evaluation report examples.
- limitations document.
- final run transcript.

Validation commands:

- final smoke test.
- document review checklist.

Done criteria:

- project is demonstrable, explainable, and academically defensible.

Recap file:

- `reports/phases/Rebuild_17_Final_Demo_Polish_And_Academic_Evidence_Result.md`

## 23. Risk Register

| Risk | Impact | Mitigation |
|---|---:|---|

| Risk | Impact | Mitigation |
|---|---:|---|
| LLM structured output failure | High | Test early (Phase 1 spike), use Pydantic parsing, use fallback repairs, simplify schema if needed. |
| Giant graph state / checkpoint bloat | High | Use lightweight WorkflowState containing only IDs; fetch full documents from DB via services. |
| Long workflow HTTP timeout | High | Implement polling endpoints (`/status`); do not hold POST connections open. |
| Interactive vs demo mode confusion | Medium | Explicitly label mode in UI and API requests; separate seeded inputs from manual flows. |
| Progress desync after adaptation | High | Diff curriculum versions; preserve completed topic progress; explicitly supersede old topics. |
| Duplicate graph runs from retries | Medium | Require idempotency keys for workflow triggers. |
| Seed corpus too small | Medium | Mandate minimum 40-60 curated resources specifically covering canonical concepts. |
| Evaluation formulas too subjective | Low | Rely heavily on deterministic database metrics (Coverage, Alignment) over LLM-as-a-judge. |
| Frontend/backend contract drift | High | Use defined DTOs and Payload schemas from Rebuild-0B. |
| Overclaiming RAG without embeddings | Low | Use precise academic terminology ("curated corpus metadata recommendation") for v1. |
 Medium | Use max revision attempts and continue with warning when capped. |

## 24. Definition Of Done For Rebuild-0B

Runtime implementation may start only when:

- This specification document exists.
- The phase result report exists.

- Mode distinction (Interactive vs Demo) defined.
- Orchestration polling endpoints defined.
- Lightweight WorkflowState defined.
- ID naming conventions defined.
- Idempotency policy defined.
- Dashboard payload schema defined.
- LLM structured-output spike added to roadmap.
- Curriculum adaptation versioning defined.
- Progress synchronization after adaptation defined.
- Seed corpus acceptance standard defined.
- Critical API DTOs field-defined.
- Risk register updated with new mitigations.

- The LangGraph node list and transitions are defined.
- Workflow constants are defined.
- WorkflowState fields are defined.
- Agent contracts are defined.
- MongoDB document schemas are field-defined.
- Repository interfaces are specified.
- Service responsibilities are specified.
- API contract plan exists.
- RAG corpus strategy has resource schema and ranking formula.
- Evaluation rubric has numeric formulas and weights.
- Adapter thresholds and allowed actions are defined.
- LLM client strategy includes mock, timeout, retry, and fallback policy.
- Frontend routes and dashboard sections are defined.
- Scope exclusions are explicit.
- Roadmap phases and done criteria are documented.
- No runtime code has been implemented as part of Rebuild-0B.
- No dependencies have been installed.



## 25. Final Recommendation

**After this Rebuild-0B Correction Pass, proceed to Rebuild-1 (Backend Foundation, Tooling, and LLM Spike).**

What should happen next:
- Begin Rebuild-1 to setup FastAPI, Pytest, and verify the university LLM can handle your JSON schemas.
- Do NOT start product or business workflow logic until Rebuild-2 and Rebuild-3 contracts and mock fixtures are implemented.
- Maintain the strict no-auth, local demo-first scope.

What should not happen yet:
- No auth, no Docker, no live deployments.
- No massive frontend build-out until backend contracts compile and mock data can be served.



---

## Source 2: Rebuild-0B Correction Pass Result

> Canonical merged reference: `docs\architecture\MAIN.md`

# Rebuild-0B Correction Pass Result

Status: Completed  
Project: PathAI  
Phase: Rebuild-0B Correction Pass  

## A. Scope

This phase performed a focused correction pass on the Rebuild-0B Architecture, Contracts, and Roadmap specification document based on external reviews. The scope was strictly documentation and specification updates. No runtime logic, backend infrastructure, or frontend components were implemented.

## B. Reviews Incorporated

This pass incorporated critical reviews from external AI models (GLM, Gemini, Codex) and senior AI engineering best practices. The reviews verified that the architecture direction was sound but identified specific technical risks:
- `WorkflowState` bloat and checkpoint overhead.
- Frontend polling mechanics for long-running workflows.
- LLM structured-output reliability (specifically the University-hosted LLM).
- Progress synchronization after curriculum adaptations.

## C. Files Reviewed

Safe file reading was performed on the existing architecture specification to determine correct injection points.
- `docs/architecture/PathAI_Global_Architecture_And_Implementation_Blueprint.md`



## D. Files Updated

**Updated:**
- `docs/architecture/PathAI_Global_Architecture_And_Implementation_Blueprint.md`

**Created:**
- `reports/phases/Rebuild_0B_Correction_Pass_Result.md`

## E. Main Corrections Added

The following core architectural corrections and enhancements were integrated:
1. **Execution Modes Defined:** Clear distinction between `Interactive Mode` and `Deterministic Demo Mode`.
2. **Lightweight Workflow State:** Redesigned `WorkflowState` to store string IDs and summaries rather than full nested Pydantic documents, preventing graph state bloat.
3. **Orchestration Polling:** Replaced blocking HTTP POST assumptions with a robust `/api/v1/orchestration/runs/{run_id}/status` polling contract.
4. **LLM Structured Output Spike:** Adjusted the roadmap (Rebuild-1) to prioritize a spike confirming the University-hosted LLM can successfully return complex JSON schemas before committing to them.
5. **Idempotency & Naming Conventions:** Defined strict ID prefixes (e.g., `goal_`, `run_`) and established explicit idempotency rules for API routes and workflow retries.
6. **Curriculum Versioning & Progress Sync:** Formalized how adaptation creates a new curriculum revision, preserving `TopicProgress` for untouched topics and updating the `ProgressState` differential.
7. **Seed Corpus Acceptance Standard:** Added a rigorous acceptance criteria for RAG v1 (minimum 40-60 curated resources, specific fields, and diversity markers) and explicitly categorized embeddings as a v2 enhancement.
8. **Dashboard Payload Schema:** Introduced a frontend-friendly read-model schema (`DashboardPayload`) mapped by the DashboardService.
9. **Observability Rules:** Mandated `request_id`/`run_id` trace propagation, structured logging per workflow node, and safe frontend error handling.
10. **Evaluation Tuning:** Refined the Quiz Alignment metric to specifically check alignment against weak concepts in the knowledge map.
11. **Roadmap Restructuring:** Merged the Mock LLM fixtures with the Core Schemas phase to validate schemas immediately.

## F. Remaining Open Questions

- Does the University-hosted LLM support a strict JSON mode/function calling capability, or will it require a heavy LLM parser/repair pipeline? (To be tested in Rebuild-1).
- Should the `POST /api/v1/orchestration/runs/{run_id}/cancel` endpoint be prioritized for the local demo, or safely deferred until a later production phase?

## G. Validation Performed

Validation was documentation-based:
- Validated injection of all required 25 correction points into the architecture document.
- Safely searched and updated the markdown document using programmatic text replacement without corrupting surrounding sections.
- Verified file creation and correct path structure.

## H. Not Done

The following were intentionally NOT done, adhering strictly to scope:
- No backend runtime logic was implemented.
- No frontend runtime logic was implemented.
- No dependencies (`npm install` / `pip install`) were executed.
- No authentication or deployment infrastructure (Docker, CI/CD) was implemented.
- The `.env` file was not copied, modified, or exposed.

## I. Next Recommended Phase

**Rebuild-1: Backend Project Foundation, Tooling, And LLM Spike**

The architecture contracts are now implementation-ready. The next phase will establish the FastAPI application skeleton, testing foundation, and explicitly test the University-hosted LLM's capacity for complex JSON output. No product business logic should be written until Rebuild-2 schemas and Mock fixtures are in place.



---

## Source 3: Rebuild-0B Architecture Contracts And Roadmap Result

> Canonical merged reference: `docs\architecture\MAIN.md`

# Rebuild-0B Architecture Contracts And Roadmap Result

Status: Completed  
Project: PathAI  
Created: 2026-06-23  

## A. Scope

This phase created a detailed architecture and implementation-contract specification for PathAI Rebuild-0B.

The scope was documentation only:

- Define architecture principles.
- Define system layering.
- Define canonical no-auth demo journey.
- Define LangGraph workflow contracts.
- Define workflow state schema.
- Define agent input/output contracts.
- Define MongoDB document schemas.
- Define repository and service contracts.
- Define no-auth API contract plan.
- Define RAG corpus strategy.
- Define evaluation rubric.
- Define adapter/replanning rules.
- Define LLM client strategy.
- Define frontend information architecture.
- Define UI product direction.
- Define testing strategy.
- Define implementation roadmap.
- Define risk register.
- Define Rebuild-0B done criteria.

No backend runtime implementation, frontend runtime implementation, dependency installation, authentication, Docker, or deployment work was performed.

## B. Files Reviewed

The task instructions were reviewed from the attached pasted request.

Safe directory listings were performed for:

- `docs`
- `docs/architecture`
- `reports`
- `reports/phases`

The `.env` file was not  printed, copied, modified, or exposed.

## C. Files Created or Updated

Created:

- `docs/architecture/PathAI_Global_Architecture_And_Implementation_Blueprint.md`
- `reports/phases/Rebuild_0B_Architecture_Contracts_And_Roadmap_Result.md`

No runtime source files were created or modified.

## D. Main Architecture Decisions Captured

The specification captures these decisions:

- The frontend talks only to the backend API.
- API routes call services.
- Services own business logic.
- Repositories own persistence abstraction.
- MongoDB stores durable state.
- Agents do not directly own persistence.
- Agents receive structured inputs and return structured outputs.
- LangGraph coordinates workflow execution, not storage.
- A local no-auth demo is the first target.
- Fake repositories and mock LLM behavior should support deterministic tests.
- The first demo uses the canonical goal: "Learn RAG systems for an AI engineering graduation project".
- RAG v1 uses a curated seed corpus and metadata ranking before embeddings.
- Evaluation uses deterministic numeric rubrics plus critic review.
- Adapter/replanning uses explicit thresholds and bounded allowed actions.
- Authentication, deployment, Docker, CI/CD, live web scraping, fine-tuning, and production multi-user logic are postponed.

## E. Claude/Codex Recommendations Incorporated

The Rebuild-0B document incorporates the major recommendations from the prior architecture reviews:

- Concrete LangGraph node list, edges, conditional transitions, loop caps, and failure behavior.
- Field-level MongoDB document schemas.
- Explicit assessment loop exit logic.
- Explicit critic revision loop logic.
- Curated RAG corpus strategy with resource schema and ranking formula.
- Explicit adapter thresholds and allowed adaptation actions.
- Numeric evaluation formulas, weights, and pass/fail thresholds.
- LLM timeout, retry, structured parsing, mock, and fallback policies.
- Frontend route map and information architecture.
- Deterministic canonical demo path.
- Scope control through breadth-first implementation phases.

## F. Remaining Open Questions

Open questions to resolve before or during Rebuild-1 and Rebuild-2:

- Whether MongoDB Atlas should be connected in Rebuild-4 only, or partially configured earlier with integration tests skipped by default.
- Whether the canonical demo should expose one-click full pipeline execution first or manual step-by-step execution first.
- Exact final list of seed corpus resources.
- Whether embeddings will be included before final academic submission or documented as a future enhancement.
- Whether the frontend design system should use a UI library or custom components.
- Exact university-hosted LLM API shape and structured-output support.
- Whether graph checkpoint resume is needed before final demo or can remain a post-demo enhancement.

## G. Validation Performed

Validation performed during this documentation phase:

- Confirmed target documentation directories exist through safe directory listing.
- Created the Rebuild-0B architecture/contracts document.
- Created this Rebuild-0B phase result document.
- Verified both created Markdown files exist.
- Verified the architecture document contains required sections 1 through 25.
- Verified this result document contains required sections A through I.


No backend tests, frontend tests, dependency installs, database calls, LLM calls, Docker commands, or deployment commands were run.

## H. Not Done

The following were intentionally not done:

- No backend runtime logic.
- No frontend runtime logic.
- No dependency installation.
- No `npm install`.
- No `pip install`.
- No authentication.
- No JWT/login/register.
- No Docker.
- No deployment.
- No CI/CD.
- No live web scraping.
- No live LLM calls.

- No secret exposure.

## I. Next Recommended Phase

The next recommended phase is Rebuild-1: Backend Project Foundation And Tooling.

Rebuild-1 should only establish the backend foundation, app skeleton, settings skeleton, health endpoint, and test tooling. It should not jump into full product workflow implementation before Rebuild-2 core schemas and contracts are implemented.



