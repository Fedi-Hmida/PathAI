# PathAI — Pending Work Reference

**Purpose:** a single up-to-date reference for what's done, what's in flight, and what's
genuinely missing — written for picking this project back up in a fresh chat session with no
prior context. Last updated: 2026-07-20, after `ui_ux_implementation_plan.md` Steps 1–9.

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
| B5 step 3 | Wired quiz generation into per-user `generate()` — real `QuizDTO` + scored `QuizAttemptDTO`, fresh IDs via `create_or_replace`, deleted the service-layer RAG-demo `target_concepts` fallback, transient (not persisted) progress-state seed for first-time learners | Rebuild-37 |
| — | Threaded the generated quiz attempt into the evaluation agent call — `generate()` now builds the quiz before the evaluation report and passes the real `quiz_attempt` in, so `quiz_alignment` and related metrics/recommendations stop scoring a real quiz as absent | Rebuild-37 follow-up |

All five detoxed deterministic agents (curriculum, critic, knowledge-map, assessment, quiz) are
now genuinely topic-general — verified with synthetic non-RAG unit tests plus live HTTP
verification for non-RAG goals. `generate()` now produces all five per-user artifacts (knowledge
map, curriculum, critic review, evaluation report, quiz + attempt) in dependency order (quiz before
evaluation, so evaluation sees real quiz data); `dashboard.quiz_summary` is populated, not `None`.
Offline suite: 442 passed / 26 skipped, ruff + mypy clean.

## 2. Backend — in flight, approved, not yet coded

Nothing queued right now — see §3 for the next real gaps and §7 for suggested ordering.

## 3. Backend — real gaps beyond Rebuild-37 (from the audit, still open)

- **Resources are not regenerated per-user at all** — `WorkspaceGenerationService.generate()`
  explicitly skips them: "resources are still RAG-corpus-blocked, Rebuild-16"
  (`workspace_generation.py:103-105`). This isn't just a wiring gap like quiz — `app/rag/` is
  still a genuinely empty package (per `CLAUDE.md`), so there's no real curation/ranking logic to
  call yet. This is a bigger lift than Rebuild-37, not a same-day fix.
- **Progress is not persisted per-user** — only ever constructed transiently, as of Rebuild-37 as a
  minimal, in-memory seed purely for quiz generation's benefit (`_progress_state_for_quiz` in
  `workspace_generation.py`). No real progress-tracking loop exists.
- **Adaptation is not generated at all** — `adaptation_summary` stays `None`; no adaptation agent
  is invoked from `generate()` or anywhere in the per-user path (`evaluation_agent.evaluate()` is
  still called with `adaptation_event=None` — this is the one artifact evaluation still honestly
  scores as absent, since adaptation generation itself doesn't exist yet).
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
  have shown real data since Rebuild-33; Quiz tile has shown real data since Rebuild-37 (verified
  live via the API — no browser-automation tool was available to screenshot it directly).
- Knowledge-map detail page `/knowledge-map/[id]` — full concept graph.
- Curriculum detail page `/curriculum/[id]` — weeks/topics, embeds per-topic resources.
- Orchestration run status page `/orchestration/[runId]`.
- Goal detail `/goal/[goalId]`, Critic Review detail `/critic/[criticReviewId]`, Quiz Results
  `/quiz/[quizId]/attempts/[attemptId]`, Resources Browser `/resources/[curriculumId]`, Progress
  Tracking `/progress/[progressId]`, and Adaptation Detail `/adaptation/[adaptationId]` — all six
  built and wired into the live sidebar (`app-shell.tsx`) per
  `docs/roadmap/ui_ux_implementation_plan.md` Steps 2–9; see §5 for what's still open.

## 5. Frontend — missing (= audit finding B10, P5 scope)

This was a **named, pre-existing audit finding**: `reports/audits/...md` B10 — "8 sidebar items are
dead placeholders... Data exists (as demo-clone) but no screen to view/verify it," remediation
scoped as **P5 — Wire or retire the 8 'Coming soon' screens** (`app-shell.tsx`, `COMING_SOON_LINKS`).

**Closed for 6 of the 8** (`docs/roadmap/ui_ux_implementation_plan.md` Steps 1–9): Goal, Critic
Review, Quiz Results, Resources Browser, Progress Tracking, and Adaptation Detail all now have real
pages and a real `lib/api/*.ts` client, wired into the live sidebar with each link resolving its ID
from `artifact_ids` and rendering an honestly-disabled placeholder when the ID is absent (same
pattern the pre-existing Knowledge Map/Assessment/Curriculum links already used). Progress and
Adaptation's *pages* are done, but their real backing data still doesn't exist for a real per-user
run — see §3 ("Progress is not persisted per-user" / "Adaptation is not generated at all") for why
— so their sidebar links stay disabled today. That's the correct, expected state, not a bug: once
their own backend phases land, the same links activate automatically with no frontend rework.

**Still open — 2 of the 8:**

| Screen | API client | Backing data today |
|---|---|---|
| Evaluation report detail | none (`lib/api/evaluation.ts` missing) | **real** since Rebuild-33 — just has no page (no design exists in the `UI_UX/` bundle for it either, per Steps 1–9's OQ1) |
| Agents | none | **no backend support at all** — stays an honestly-disabled "Coming soon" placeholder, per P5's own scope ("remove/disable-with-honest-reason," not build) |

Evaluation can be built any time — its backing data has been real since Rebuild-33, so it's not
blocked on further backend work, only on a design (or a from-scratch build per OQ1's option (b): a
Critic-radar-style page deriving from `EvaluationMetricScores`'s 9 metrics).

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

1. ~~Quiz + Critic + Evaluation detail pages~~ — Quiz and Critic shipped (Steps 4–5, 3 of
   `ui_ux_implementation_plan.md`); Evaluation still open, see §5.
2. ~~Adaptation/Resources/Progress/Goal pages + Agents retirement~~ — Goal/Resources/Progress/
   Adaptation shipped (Steps 2, 6–8); Agents stays an honestly-disabled placeholder per P5's scope.
3. **Evaluation report detail page** (rest of P5) — data's already real (Rebuild-33); no design
   exists yet, see §5 for the build-without-design option.
4. Backend §3 items (resources/progress/adaptation generation, B9, P6, P7) as their own future
   phases — bigger lifts, lower urgency than the above.
