# PathAI Engineering Rules

Status: Mandatory execution rulebook  
Project: PathAI  
Applies to: Every future prompt, phase, implementation task, review, audit, and recap  

## 1. Purpose

`RULES.md` defines the mandatory engineering, architecture, security, validation, documentation, and phase discipline rules for the PathAI rebuild.

This document is a restriction document, not optional advice. Future work must comply with it unless a later explicit user instruction updates the rules.

The purpose of these rules is to keep PathAI:

- aligned with the canonical architecture.
- secure with respect to secrets and environment files.
- phase-disciplined.
- testable.
- modular.
- reviewable.
- academically defensible.
- implementation-ready without uncontrolled scope expansion.

## 2. Mandatory References For Every Task

Every future PathAI prompt, phase, implementation task, review, and audit must use:

- `docs\architecture\MAIN.md` as the canonical architecture blueprint.
- `docs\architecture\RULES.md` as the mandatory execution rulebook.

Required behavior:

- Read and respect `MAIN.md`.
- Read and respect `RULES.md`.
- Treat `RULES.md` as mandatory restrictions, not suggestions.
- Confirm in each phase recap that the work respected `MAIN.md` and `RULES.md`.
- Do not proceed with implementation decisions that contradict `MAIN.md` or `RULES.md` unless the user explicitly approves an architecture update.

## 3. General Engineering Rules

- Respect the existing project structure.
- Keep changes scoped to the requested phase.
- Do not implement future phases early.
- Do not mix backend, frontend, AI, persistence, and UI work unless explicitly required by the phase.
- Do not create large messy files.
- Prefer small, focused modules.
- Separate schemas, services, repositories, agents, orchestration, API routes, and tests.
- Do not put business logic inside API routes.
- Do not put persistence logic inside agents.
- Do not let the frontend call MongoDB, LLMs, or agents directly.
- Use typed contracts and explicit DTOs.
- Keep agents structured-output only.
- Add tests appropriate to the phase.
- Validate with real commands and report exact results.
- Do not claim success unless validation passes.
- Preserve `.env`; never read, print, copy, modify, or expose secrets.
- Do not implement authentication, Docker, or deployment unless explicitly requested.
- Preserve `.git`.
- Avoid unrelated refactors.
- Avoid changing files outside the phase scope.
- Prefer clear names over clever abstractions.
- Keep implementation breadth-first until the no-auth demo works.

## 4. Backend Rules

- API routes should only validate request boundaries and call services.
- Services own business logic.
- Repositories own persistence abstraction.
- Models and schemas must stay separate from service logic.
- Use fake repositories before Mongo-backed repositories unless the phase says otherwise.
- Use mock LLM clients in tests.
- No default tests should require real LLM, network, or MongoDB unless explicitly marked.
- Add health/readiness endpoints only if in scope.
- Keep files small and cohesive.
- Keep FastAPI dependencies explicit and minimal.
- Keep settings access centralized in a settings layer.
- Do not import database clients directly into API routes.
- Do not call agents directly from API routes.
- Do not return internal database documents directly if an API DTO is required.
- Keep status enums and IDs validated.
- Keep test fixtures deterministic.

## 5. AI / Agent / LangGraph Rules

- Agents must not write to the database.
- Agents must return structured Pydantic outputs.
- Agent prompts, contracts, parsing, and validation must be separated.
- LangGraph state should stay lightweight: IDs, statuses, counters, summaries.
- Full artifacts must live in repositories, not graph state.
- Add loop caps and failure behavior.
- Add deterministic mock outputs for tests.
- Treat LLM output as untrusted data.
- Validate all LLM output before saving or displaying.
- Do not pass huge persisted artifacts into prompts unless explicitly needed.
- Do not let agents decide persistence policy.
- Do not let graph nodes bypass services for persistence.
- Add structured failure outputs for agent errors.
- Add retry caps for malformed or timed-out LLM responses.
- Keep default orchestration tests independent of live LLM calls.

## 6. Frontend Rules

- Frontend only talks to backend API.
- Use backend DTOs and API client helpers.
- Do not hard-code fake data unless explicitly labeled as demo/sample.
- Handle loading, empty, error, offline, and expired-ID states.
- Keep UI consistent with the PathAI design direction.
- Avoid debug-heavy UI in learner-facing screens.
- Keep components small and feature-based.
- Do not store secrets in frontend state or localStorage.
- LocalStorage may store only non-sensitive demo IDs such as `run_id` or `goal_id`.
- Do not call MongoDB, LLMs, agents, or internal backend modules from frontend code.
- Do not show raw stack traces in learner-facing screens.
- Use clear learner-facing error messages.
- Keep API client behavior centralized.
- Keep route-level logic thin.

## 7. Security Rules

- Never read, print, copy, expose, or overwrite `.env`.
- Never commit or create files containing secrets, tokens, API keys, MongoDB URIs, passwords, private keys, or real credentials.
- Use environment variable names only, never real values.
- Keep `.env.example` secret-free.
- Add or preserve `.gitignore` rules for `.env`, local caches, logs, virtual environments, build outputs, and generated secret-bearing files.
- Do not log secrets or full request headers.
- Do not return secrets in API responses.
- Redact sensitive values in errors, logs, test output, and documentation.
- Do not hard-code credentials in code, tests, docs, fixtures, or frontend files.
- Do not expose backend internals, stack traces, or raw provider errors to the frontend.
- Use safe, generic frontend error messages.
- Validate all incoming API payloads with Pydantic schemas.
- Reject unknown or malformed payloads where appropriate.
- Add limits for text inputs such as goal text, assessment answers, and prompt-bound content.
- Treat LLM output as untrusted data; validate it before saving or displaying.
- Never let LLM output directly control file paths, shell commands, database queries, or system prompts.
- Keep agents persistence-free; services validate and decide what is saved.
- Prevent duplicate side effects with idempotency keys where needed.
- For local no-auth mode, make clear it is development/demo mode, not production security.
- Do not implement authentication, JWT, password hashing, sessions, or protected routes unless the phase explicitly requests it.

## 8. Backend Security Rules

- Load config only through a settings layer.
- Do not print loaded config values.
- Health endpoints may show status, but not secret values.
- Readiness endpoints may say configured/not configured, but must not expose connection strings.
- Database errors should be logged safely and returned as sanitized messages.
- CORS should be local-development scoped first, not wildcard production policy.
- Add request size limits where practical.
- Add clear validation for IDs and status enums.
- Avoid leaking internal exception details through API responses.
- Keep stack traces out of frontend-facing payloads.
- Validate route parameters.
- Validate body payloads.
- Validate query parameters.
- Use safe defaults for local development.

## 9. AI Security Rules

- Treat user input as untrusted prompt content.
- Separate system/developer prompts from user-provided learning goals and answers.
- Do not allow user text to override system instructions.
- Validate all structured LLM outputs against schemas.
- On schema failure, retry or fail safely; do not save invalid output.
- Do not use LLM output as trusted authority for security decisions.
- Do not include secrets or hidden config in prompts sent to the LLM.
- Do not include `.env` values in prompts.
- Do not include raw internal errors in prompts unless safely redacted.
- Keep prompt templates versionable and reviewable.
- Keep parser failures observable but sanitized.

## 10. Frontend Security Rules

- Do not store secrets in localStorage/sessionStorage.
- LocalStorage may store only non-sensitive demo IDs such as `run_id` or `goal_id`.
- Do not expose `.env` values to client-side code.
- Only use explicitly public frontend env vars when needed.
- Display sanitized error messages.
- Do not show raw stack traces or backend exception details.
- Do not expose provider details unnecessarily.
- Do not place credentials in browser-visible source.
- Do not include secret-like values in screenshots, fixtures, or demo data.

## 11. File Size And Modularity Rules

- Avoid giant files.
- Split large logic by responsibility.
- Prefer feature modules.
- Prefer one clear responsibility per file.
- If a file grows too large, extract schemas, helpers, services, components, or tests.
- Do not duplicate contracts across unrelated files.
- Keep tests focused and readable.
- Keep API schemas separate from service implementations.
- Keep database models separate from API route code.
- Keep prompt templates separate from parsing and validation logic.
- Keep frontend feature components separate from generic UI components.
- Avoid catch-all utility files unless the helper is genuinely shared.
- Avoid copy/paste contracts that drift over time.

## 12. Phase Discipline Rules

- Every phase must have a clear scope.
- Every phase must state what is intentionally not done.
- Every phase must avoid future-phase implementation.
- Every phase must create or update a result recap under `reports\phases`.
- Every phase must validate with appropriate commands.
- Every phase must report exact validation results.
- Every phase must mention compliance with `MAIN.md` and `RULES.md`.
- Every phase must preserve `.env` and secrets.
- Every phase must avoid unrelated refactors.
- Every phase must keep implementation aligned with the roadmap in `MAIN.md`.
- Every phase must state the next recommended phase.
- If validation cannot run, the recap must explain exactly why.

## 13. Required Phase Recap Structure

Every phase recap must use this mandatory structure:

```text
A. Scope
B. MAIN.md / RULES.md Compliance
C. Files Created or Updated
D. Work Completed
E. Validation Commands And Results
F. Security / Secret Handling
G. Not Done / Intentionally Postponed
H. Remaining Risks
I. Next Recommended Phase
```

Recaps must be honest. They must not claim validation or implementation that did not happen.

## 14. Validation Rules

- Use real commands where applicable.
- Do not fake validation.
- If tests cannot run, explain exactly why.
- If dependencies are missing, do not pretend tests passed.
- Keep default tests independent of real LLM, network, or MongoDB unless explicitly configured.
- Report warnings honestly.
- Do not claim success if validation fails.
- Report exact validation commands and outcomes.
- Prefer focused validation commands for the touched area.
- Do not run expensive or unrelated validation unless the phase requires it.
- Do not run commands that require secrets unless explicitly approved and safe.
- Do not run backend/frontend tests during documentation-only phases unless explicitly requested.

## 15. Scope Exclusions Until Explicitly Requested

The following are excluded until explicitly requested:

- authentication.
- JWT/login/register.
- password hashing.
- user sessions.
- protected routes.
- Docker.
- deployment.
- CI/CD.
- production hosting.
- live web scraping.
- fine-tuning.
- advanced vector infrastructure.
- admin panels.
- production multi-user account management.
- payment or billing.
- role-based access control.
- production observability.
- mobile app.
- LMS integrations.

## 16. Final Rule

Every future PathAI task must be small, scoped, validated, secure, aligned with `MAIN.md`, and compliant with `RULES.md`.

## 17. Multi-Agent Operation Rules

Status: approved direction, not yet implemented. These rules bind any future phase that enables more than one LLM-backed agent in the same orchestration run. See `MAIN.md` §7.8 for the architectural policy this enforces.

### 17.1 What Counts As Multi-Agent

Do not describe a run as "multi-agent" in any code comment, recap, or document unless all five of the following hold:

1. Two or more agents are LLM-backed in the same orchestration run, not deterministic stand-ins.
2. A real data dependency exists between at least two of them: one agent's real LLM output is consumed as another agent's input.
3. The run is reachable by a real caller over HTTP, not only by direct Python construction in a test.
4. The run is observable and bounded: an operator can see which agents ran in LLM mode, how many LLM calls were made, and how long the run took, under a hard per-run ceiling.
5. The specific combination has been validated as a combination, not merely as independent single agents.

If 2+ agents are active but any of points 2 through 5 fails, call it what it is — parallel single-agent activation — and say so plainly.

### 17.2 Validated-Combination Allowlist

- Zero enabled LLM agents, or exactly one, remains allowed by default. This is the current behavior and must not regress.
- A combination of two or more LLM agents may only be activated if that exact combination appears in an explicit, code-defined allowlist.
- Each allowlisted combination must have its own phase, its own interaction test, and its own recap before being added. Adding a combination to the allowlist without an interaction test behind it is forbidden.
- Any requested combination of 2+ agents that is not allowlisted must raise `ActivationConfigError` at construction time, with a sanitized message naming the rejected combination and the phase that would need to land first. It must never silently activate, and never silently degrade to single-agent or deterministic mode.
- Rationale: Rebuild-14D shipped a defect where per-agent flags silently activated a real, never-integration-tested LLM agent. The allowlist exists so that the same class of defect cannot reappear at the combination level.

### 17.3 Run-Level Budget

- Any run with two or more LLM agents active must execute under a run-level budget: a maximum total number of LLM calls per run and a maximum wall-clock duration per run.
- The run-level budget is enforced independently of, and in addition to, any single agent's own retry and timeout policy. An agent's `LLMRetryPolicy` bounds one agent; the run budget bounds the run.
- Exceeding the budget must fail safe: remaining agents degrade to their deterministic fallback. It must not hard-fail the orchestration run, consistent with the existing per-agent fallback policy.
- Budget exhaustion must emit a sanitized, observable event through the existing `LLMReliabilityObserver` boundary. It must not be silent.

### 17.4 Interaction Tests Are A First-Class Category

- Multi-agent interaction tests use the suffix `*_agent_interaction.py`, taking their place alongside the existing `*_behavior.py`, `*_events.py`, `*_orchestration.py`, and `*_scope_security.py` conventions.
- An interaction test must assert on the handoff itself: that agent B's real LLM call consumed agent A's real LLM output, not agent A's deterministic fixture. Asserting that both agents merely ran is insufficient.
- Interaction tests are deterministic and offline. They use `FakeLLMClient` scenarios, exactly like every existing LLM-agent test. They must never require a real provider, network, or credentials.

### 17.5 Existing Rules Are Unchanged At Multi-Agent Scale

Multi-agent operation grants no exemption from any rule in this document. Restated explicitly because these are the rules most likely to be rationalized away while wiring several agents together:

- Layering (§3, §4) holds. Do not loosen the API/agent or orchestration/LLM boundaries to make multi-agent wiring more convenient. Orchestration must not import `app.llm`; helpers that need it live under `app/agents/llm/`, the only allowlisted directory.
- Agents remain persistence-free and structured-output only (§5). Services still decide what is saved.
- All LLM output remains untrusted and must be schema-validated before use, including — especially — when one agent's output becomes another agent's input (§5, §9).
- Redaction (§7, §9) applies to every new event, error, and log line the run-level budget introduces.
- The default test suite must still require no real LLM, no network, and no MongoDB (§4, §14).
- Phase discipline (§12) holds: one combination per phase, each with its own recap, no batching.
