# PathAI — Pending Work Reference

**Purpose:** a single up-to-date reference for what's done, what's in flight, and what's
genuinely missing — written for picking this project back up in a fresh chat session with no
prior context. Last updated: 2026-07-17, after Rebuild-36 (pushed, `67959fa`).

Source of truth for anything below: read the actual code before trusting this doc — it decays.
The canonical audit this tracks is `reports/audits/2026-07-13_end_to_end_provenance_audit.md`
(findings B1–B11, remediation phases P1–P7). `reports/phases/rebuild-N/` holds a recap per shipped
phase but **is gitignored** — it exists on disk in this workspace but won't show up if you clone
the repo fresh elsewhere; the highest-numbered `rebuild-N/` there is the real current status.

---

## 1. Backend — done (audit track P1–P4, partial)

| # | What | Phase |
|---|------|-------|
| B1/B2/B8 | Real Groq LLM gateway, correct model id, assessment+KM+curriculum LLM flags on | earlier (pre-32) |
| B7/P3 | Assessment/KM/curriculum genuinely topic-general (real goal-driven output, not RAG) | Rebuild-29 |
| B4/P2 | LLM failures fail loud (503 `generation_unavailable`) instead of silent RAG fallback | Rebuild-30 |
| — | Bounded in-band self-correction retry for schema-invalid LLM output | Rebuild-31 |
| B5 step 1 | Stopped cloning the RAG demo into new workspaces; `generate()` builds real KM + curriculum | Rebuild-32 |
| B5 step 2 | `generate()` also builds real critic review + evaluation report; detoxed critic's RAG `PREREQUISITES` table | Rebuild-33 |
| — | Detoxed deterministic knowledge-map agent's RAG `_LABELS`/`_RECOMMENDED_ACTIONS`/`_PREREQUISITES`/ordering | Rebuild-34 |
| B3/B6 | Detoxed deterministic assessment agent — real self-rating questions, real scoring (was previously a fixed lookup that never read the learner's actual answer) | Rebuild-35 |
| B3-class | Detoxed deterministic quiz agent — curriculum-derived MC questions, real per-quiz scoring (also fixed grading being keyed to a global bank instead of the actual administered quiz) | Rebuild-36 |

All five detoxed deterministic agents (curriculum, critic, knowledge-map, assessment, quiz) are
now genuinely topic-general — verified with synthetic non-RAG unit tests plus live HTTP
verification for non-RAG goals. Offline suite: 440 passed / 26 skipped, ruff + mypy clean as of
Rebuild-36.

## 2. Backend — in flight, approved, not yet coded

### Rebuild-37 — wire quiz generation into the live per-user `generate()` flow
`WorkspaceGenerationService.generate()` (`backend/app/agents/services/workspace_generation.py:44-57`)
currently builds knowledge_map + curriculum + critic_review + evaluation_report per real user, but
its own docstring says quiz is **deliberately** excluded — `dashboard.quiz_summary` is `None`
forever for a real workspace today.

**Confirmed mechanism (already verified this session, don't re-derive):**
- `QuizAgentService.build()` (`app/agents/services/quiz.py:32-116`) needs a `ProgressStateDTO` and
  derives `target_concepts` from `progress_state.weak_concepts or demo.QUIZ.target_concept_ids`
  (line 42) — that fallback is a live RAG-demo leak: a first-time learner with no progress yet
  would silently inherit the canonical demo's own concept list.
- `quiz_id`/`quiz_attempt_id` are hardcoded to `demo.QUIZ_ID`/`demo.QUIZ_ATTEMPT_ID` (lines 54, 74)
  — no explicit-ID param exists yet, unlike KM/curriculum/critic/evaluation. Persistence uses
  `create_or_get`, not `create_or_replace` — regeneration would silently keep a stale quiz.
- `ProgressStateDTO.topic_progress` requires `min_length=1` — a "no history yet" progress state
  needs at least one `TopicProgressDTO` entry (e.g. the curriculum's first topic, `NOT_STARTED`,
  `completion=0.0`), it can't be a literal empty list.
- `ProgressService.list_by_goal_id(goal_id)` already exists for checking prior progress.

**Approved design (Decision #1 = Option A, confirmed with the user this session):**
On `generate()`, look up existing progress via `list_by_goal_id`; if none exists, construct an
in-memory (not persisted — progress-tracking itself stays out of scope) `ProgressStateDTO` with
`weak_concepts=[]` and one `NOT_STARTED` topic-progress entry for the curriculum's first topic.
Delete the `demo.QUIZ.target_concept_ids` fallback in `QuizAgentService.build()` so an empty
`weak_concepts` falls through to the curriculum's own concept ids (the deterministic quiz agent
already handles that correctly post-Rebuild-36). Add explicit `quiz_id`/`quiz_attempt_id` params +
switch to `create_or_replace`, mirroring the Rebuild-33 pattern exactly.

**Full mission-brief prompt for this phase was drafted and is ready to hand to a fresh session —
see the conversation history, or regenerate one in the same style if it's not at hand; the design
above plus the CURRENT MECHANISM section is enough to reconstruct it.**

## 3. Backend — real gaps beyond Rebuild-37 (from the audit, still open)

- **Resources are not regenerated per-user at all** — `WorkspaceGenerationService.generate()`
  explicitly skips them: "resources are still RAG-corpus-blocked, Rebuild-16"
  (`workspace_generation.py:103-105`). This isn't just a wiring gap like quiz — `app/rag/` is
  still a genuinely empty package (per `CLAUDE.md`), so there's no real curation/ranking logic to
  call yet. This is a bigger lift than Rebuild-37, not a same-day fix.
- **Progress is not persisted per-user** — only ever constructed transiently (and, post-Rebuild-37,
  only as a minimal seed for quiz generation's benefit). No real progress-tracking loop exists.
- **Adaptation is not generated at all** — `adaptation_summary` stays `None`; no adaptation agent
  is invoked from `generate()` or anywhere in the per-user path.
- **B9** (Medium, data lifecycle) — `knowledge_map.assessment_session_id` can dangle at seed time;
  tolerated today because `dashboard.py` swallows the `NotFoundError` and shows
  `assessment_summary=None` until a live session exists. Not urgent, but a known rough edge.
- **P6** — reset cascade doesn't clean up superseded artifacts; no explicit "pending generation" vs
  "no data yet" distinction in dashboard summaries; synchronous generation could move to a
  background job with progress UI if latency becomes a problem (B8-adjacent).
- **P7** — no opt-in live end-to-end test (register → real goal → diagnostic → generate → dashboard,
  asserting zero RAG) exists as an automated, repeatable check. All live verification so far has
  been done manually per-phase via Playwright scripts in the scratchpad, not committed as a
  reusable opt-in test.
- **MAIN.md §7.3 bounded loops** — `should_continue_assessment` and `should_adapt` are still
  unimplemented in the orchestration graph (scoped as a future rebuild, not urgent).

## 4. Frontend — done

The frontend is **substantially built**, contrary to `CLAUDE.md`'s architecture section (which
says "empty dirs with `.gitkeep`" — that line is stale and should probably be corrected in a
future doc-maintenance pass). Confirmed working end-to-end:

- Auth: register/login/account, real JWT flow.
- Goal intake: `/workspace` (create/reset).
- Live diagnostic assessment: `/assessment/live/[id]` — real self-rating flow (Rebuild-35), auto-
  calls `generate()` on completion, routes to dashboard.
- Dashboard `/dashboard/[runId]`: goal header, run status, adaptation banner, completion ring,
  next-action card, curriculum week list, knowledge-map card, and **KPI tiles for Quiz / Critic /
  Evaluation / Resources** (`app/dashboard/[runId]/page.tsx:164-215`) — Critic and Evaluation tiles
  have shown real data since Rebuild-33; Quiz tile is wired but has nothing real behind it until
  Rebuild-37 ships.
- Knowledge-map detail page `/knowledge-map/[id]` — full concept graph.
- Curriculum detail page `/curriculum/[id]` — weeks/topics, embeds per-topic resources.
- Orchestration run status page `/orchestration/[runId]`.

## 5. Frontend — missing (= audit finding B10, P5 scope)

This is a **named, pre-existing audit finding**, not a new discovery: `reports/audits/...md` B10 —
"8 sidebar items are dead placeholders... Data exists (as demo-clone) but no screen to view/verify
it," remediation scoped as **P5 — Wire or retire the 8 'Coming soon' screens**
(`app-shell.tsx:38-47`, `COMING_SOON_LINKS`).

Confirmed still true this session — **no page and no `lib/api/*.ts` client exist at all** for:

| Screen | API client | Backing data today |
|---|---|---|
| Quiz detail | none (`lib/api/quiz.ts` missing) | none yet (blocked on Rebuild-37) |
| Critic review detail | none (`lib/api/critic.ts` missing) | **real** since Rebuild-33 — just has no page to show it |
| Evaluation report detail | none (`lib/api/evaluation.ts` missing) | **real** since Rebuild-33 — same gap |
| Adaptation history | none (`lib/api/adaptation.ts` missing) | none (adaptation isn't generated at all, see §3) |
| Resources (standalone) | `resource.ts` exists but is only used inside the curriculum page | none per-user yet (see §3) |
| Progress (standalone) | `progress.ts` exists but only feeds the dashboard ring/next-action card | none persisted yet (see §3) |
| Goal (standalone) | none | goal exists, just no dedicated screen beyond `/workspace` |
| Agents | none | **no backend support at all** — P5's own scope says "remove/disable-with-honest-reason," not build |

Per the original P5 scope: build real pages for the ones with real endpoints (Goal, Progress,
Resources, Quiz, Critic, Evaluation), remove or honestly disable Agents (no backend exists for it).
**Sequencing recommendation (discussed with the user, not yet started):** finish Rebuild-37 first
so the Quiz detail page has real data to render before building it; Critic/Evaluation detail pages
could be built any time since their data is already real.

## 6. Known repo housekeeping to be aware of

- Three pre-existing, unrelated files have sat modified-but-uncommitted across many recent
  sessions: `backend/app/tests/test_api_product_routes.py`,
  `frontend/components/curriculum/week-trail.tsx`, `frontend/components/ui/wavy-trail.tsx`. Leave
  them out of any phase commit unless the user asks about them directly — don't assume they're
  yours to clean up or revert.
- `reports/phases/` is gitignored — recaps exist locally but never appear in `git status` or on
  GitHub. Don't mistake their absence from a diff for them not existing, and don't expect them to
  be present after a fresh clone.
- Commit convention: no AI-attribution trailer, one-sentence commit messages, auto-push to `main`
  authorized once verification (tests/lint/typecheck, and live UI check for frontend work) passes
  — see `CLAUDE.md`.

## 7. Suggested next-phase order

1. **Rebuild-37** — wire quiz into `generate()` (design already approved, see §2).
2. **Critic + Evaluation detail pages** (P5, partial) — data's already real, purely additive frontend work, no backend dependency.
3. **Quiz detail page** (P5, remainder) — after Rebuild-37 ships.
4. **Adaptation/Resources/Progress/Goal pages + Agents retirement** (rest of P5) — resources/progress/adaptation pages will show honest "not yet generated" states until their own backend phases (§3) land; that's an acceptable interim per P5's own acceptance criteria ("no dead placeholder shows *fabricated* data" — an honest empty state is fine, silence via missing route is not).
5. Backend §3 items (resources/progress/adaptation generation, B9, P6, P7) as their own future phases — bigger lifts, lower urgency than the above.
