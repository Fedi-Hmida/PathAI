# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

PathAI is a personalized learning-path generator (local, no-auth demo): a learner enters a goal, completes a diagnostic assessment, gets a knowledge map and week-by-week curriculum, curated resources, quizzes, and adaptive replanning. Only the **backend** is implemented; `frontend/` is scaffolding only (empty dirs with `.gitkeep`).

The project follows a phased "rebuild" process (Rebuild-0 through Rebuild-13+, tracked under `reports/phases/rebuild-N/`). **Do not trust the status claims in `README.md` / `backend/README.md`** — they describe an early milestone (Rebuild-4) and are stale. Check `reports/phases/` for the latest phase report and read the actual code to know what's implemented.

## Architecture references (mandatory reading before non-trivial backend work)

- `docs/architecture/MAIN.md` — canonical architecture blueprint, contracts, planned folder structure, agent I/O contracts, Mongo document schemas, LangGraph node design. It is long (5000+ lines) and partly **aspirational**. `app/orchestration/graph.py` *is* a real single-pass generation pipeline — despite the `load_*` node names, every node calls a live agent through the service layer (`load_curriculum` → `agent_services.curriculum.build`, `load_critic_review` → `agent_services.critic.review`, etc.). What it does **not** implement are MAIN.md §7.3's bounded loops (`should_continue_assessment`, `should_revise_curriculum`, `should_adapt`): `_route_after_node` only continues or stops-on-failure, and the critic's findings never feed back into curriculum generation (`critic_recommendations` is always `[]`). That convergence is scoped as Rebuild-23. Similarly `app/rag/` and `app/evaluation/` are still empty packages despite being specified in MAIN.md. Verify against actual code, don't assume the doc is current.
- `docs/architecture/RULES.md` — **mandatory** engineering/security/phase-discipline rulebook. Read this before making architectural changes; it is treated as binding, not advisory.

Key rules from `RULES.md` worth internalizing (see the file for the full list):
- Strict layering: `Frontend -> API routes -> Services -> Repositories -> DB`, and separately `Services -> LangGraph orchestration -> Agents -> LLM/RAG/Evaluation`. API routes must not contain business logic, call agents, or touch persistence directly. Repositories must not call agents/LLMs. Agents must not touch persistence and must return structured (Pydantic) output only.
- Every phase is scoped, documented in a recap under `reports/phases/`, and must not implement future phases early or do unrelated refactors.
- Never read, print, copy, modify, or expose `.env`. Secrets must never appear in code, tests, fixtures, docs, or frontend files — use env var names only.
- Default test suite must not require a real LLM, network, or MongoDB. Live LLM / live provider checks are opt-in only (see below).

## Common commands

All backend commands run from `backend/`, using the project's venv:

```cmd
.venv\Scripts\python.exe -m pytest                                  # full test suite (deterministic, no network/LLM/DB)
.venv\Scripts\python.exe -m pytest app\tests\test_some_file.py -v   # single test file
.venv\Scripts\python.exe -m pytest app\tests\test_some_file.py::test_name -v   # single test
.venv\Scripts\python.exe -m ruff check app                          # lint
.venv\Scripts\python.exe -m mypy app --no-incremental               # type check
.venv\Scripts\python.exe -m compileall app                          # syntax/compile check
.venv\Scripts\python.exe -m uvicorn app.main:app --reload           # run the API locally
```

Live-LLM tests are marked `@pytest.mark.live_llm` and skipped by default (`pytestmark = pytest.mark.skipif(...)` gated on `ENABLE_LIVE_LLM_TESTS`). Do not set `ENABLE_LIVE_LLM_TESTS=true` unless you intentionally want to exercise a configured live provider:

```cmd
.venv\Scripts\python.exe -m pytest app\tests\test_live_llm_spike_optional.py -v
```

Install/update deps (editable install with dev extras):

```cmd
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

There is no frontend build yet, and no Docker/CI — those are explicitly out of scope until requested (see Scope Exclusions in `RULES.md`).

## Backend architecture

FastAPI app factory in `app/main.py` (`create_app`), settings via `app/core/settings.py` (`Settings`, pydantic-settings, `env_file=None` — config comes from real env vars, never from reading `.env` directly). Health/readiness never expose secret values (`Settings.redacted_dict()` redacts anything with `secret|token|key|password|uri` in the field name).

Layering on disk mirrors `docs/architecture/MAIN.md` §5:
- `app/api/v1/` — FastAPI routers, one per resource (`goal.py`, `assessment.py`, `knowledge_map.py`, `curriculum.py`, `resource.py`, `critic.py`, `progress.py`, `quiz.py`, `adaptation.py`, `evaluation.py`, `dashboard.py`, `orchestration.py`, `demo.py`, `health.py`), plus `router.py` (aggregation), `dependencies.py` (DI), `errors.py` (exception handlers), `responses.py`.
- `app/services/` — one service per domain area, own business logic, decide what to persist, are the **only** place that switches between deterministic and LLM-backed agent behavior.
- `app/repositories/` — persistence abstraction; currently fake/in-memory only (`repositories/fakes/`, deep-copy isolation) — no MongoDB wiring yet, despite being planned.
- `app/schemas/` — Pydantic v2 DTOs/contracts (API request/response, agent I/O, orchestration state). Mirrors the product domains 1:1 with services.
- `app/orchestration/` — LangGraph graph (`graph.py`), node implementations (`nodes.py`), lightweight `GraphState`/`WorkflowState` (`state.py`), run events (`events.py`), a runner (`runner.py`). Graph state holds IDs/status/counters only — never full documents (per `RULES.md` §5 and MAIN.md §8).
- `app/agents/` — three parallel implementations selected behind a service-layer switch:
  - `app/agents/mock/` — legacy deterministic mock agents (one file per agent: assessment, curriculum, critic, knowledge_map, resource, quiz, adaptation, evaluation, progress).
  - `app/agents/deterministic/` — newer deterministic agents, same set.
  - `app/agents/llm/` — real LLM-backed agents (currently: assessment, critic, curriculum, knowledge_map). Gated per-agent by env flags such as `PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT` (see `app/llm/config.py`, `LLM_ENV_VAR_NAMES`) — **one agent enabled at a time**, deterministic fallback stays available, per the rollout gates in `reports/phases/rebuild-13/`.
  - `app/agents/services/` — the switch/composition layer that decides which of the above an agent call actually uses; also `bundle.py`, `common.py`.
  - `app/agents/contracts.py`, `app/agents/errors.py` — shared typed I/O contracts and structured failure errors.
- `app/llm/` — provider-agnostic LLM client boundary: `client.py` (interface), `mock_client.py` / `fake_client.py` (deterministic), `live_client.py` (real provider calls, only reachable when explicitly configured), `config.py` (`LLMAdapterConfig`), `contracts.py`, `errors.py`, `retry.py`, `redaction.py` (scrubs secrets from logs/errors), `structured_output.py` / `structured_output_spike.py` (schema-validated LLM output).
- `app/rag/`, `app/evaluation/` — planned per MAIN.md (curated corpus ranking, deterministic scoring rubrics) but **currently empty packages** — do not assume ranking/scoring logic exists here yet.
- `app/fixtures/` — deterministic canonical demo fixtures (`canonical_demo.py`) used to drive the seeded no-auth demo path without live LLM calls.

### LLM provider config

`app/core/settings.py` reads `LLM_PROVIDER`, `LLM_BASE_URL`/`OPENAI_BASE_URL`/`UNIVERSITY_LLM_API_URL`, matching `*_MODEL`/`*_API_KEY` triplets, `LLM_MOCK_MODE`, `LLM_MAX_RETRIES`, `LLM_TIMEOUT_SECONDS`. `Settings.live_llm_configured` / `effective_llm_*` resolve which provider triplet is actually active. `.env.example` in `backend/` lists placeholder names only — real values live in the untracked `.env`, which must never be read or modified by Claude.

### Testing conventions

Tests live in `backend/app/tests/`, one file per behavior area, commonly split into `*_behavior.py` (service/agent behavior), `*_events.py` (orchestration event emission), `*_orchestration.py` (graph wiring), `*_scope_security.py` (boundary/security checks — e.g. `test_agent_scope_security.py` verifies agents can't reach persistence). `asyncio_mode = "auto"` is set in `pyproject.toml`, so async tests don't need explicit markers beyond `live_llm` where relevant.

## Commit conventions

Never include a `Co-Authored-By: Claude` trailer (or any similar AI-attribution trailer) in commit messages — commits should be attributed to the user only.

## Docs layout

`docs/architecture/` (MAIN.md, RULES.md — canonical), plus `docs/agents/`, `docs/api/`, `docs/database/`, `docs/decisions/`, `docs/demo/`, `docs/evaluation/`, `docs/operations/`, `docs/rag/`, `docs/roadmap/`, `docs/security/`, `docs/ui/` for topic-specific notes. `reports/phases/rebuild-N/` holds the mandatory phase recap for each rebuild phase (required structure: Scope, MAIN.md/RULES.md Compliance, Files Created/Updated, Work Completed, Validation Commands And Results, Security/Secret Handling, Not Done, Remaining Risks, Next Recommended Phase) — read the highest-numbered one to find current project status and the next planned phase.
