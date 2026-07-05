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

The `.env` file was not read, printed, copied, modified, or exposed.

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
- Confirmed no command was run to read, print, copy, or modify `.env` content.

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
- No `.env` access.
- No secret exposure.

## I. Next Recommended Phase

The next recommended phase is Rebuild-1: Backend Project Foundation And Tooling.

Rebuild-1 should only establish the backend foundation, app skeleton, settings skeleton, health endpoint, and test tooling. It should not jump into full product workflow implementation before Rebuild-2 core schemas and contracts are implemented.


