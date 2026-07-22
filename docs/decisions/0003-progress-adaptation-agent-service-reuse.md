# ADR-0003: Reuse Progress And Adaptation Agent-Services In The Real Per-User Path

**Status:** Decided, not yet implemented (implementation is Steps 9 and 11, not this step).
**Approved by:** The audit's own recommendation (`docs/roadmap/Big_Audit.md`, OQ-D, recorded
2026-07-20 — "Reuse both orphaned agent-services ... in the per-user path; only the trigger/signal
wiring + persistence decision is new"), confirmed against the actual code by this step's analysis
(2026-07-22). This is a documented recommendation Steps 9 and 11 inherit, not a unilateral final
approval of those steps' implementation — each still needs its own go-ahead when it starts.

## Context

`ProgressAgentService.build()` and `AdaptationAgentService.plan()` are real, structured,
agent-contract-respecting services. Both are wired into the agent bundle
(`app/agents/services/bundle.py:117,119`) but reachable **only** through the fixed-ID demo
orchestration path — `load_progress` and `load_adaptation` in `app/orchestration/nodes.py:302-339` —
which always falls back to `demo.CURRICULUM_ID` / `demo.PROGRESS_ID` / `demo.QUIZ_ATTEMPT_ID` when the
graph state doesn't carry a real one. Neither service is called anywhere in the real per-user path:
`WorkspaceGenerationService.generate()` builds only a transient, non-persisted progress seed
(`app/agents/services/workspace_generation.py:176-201`) and never calls the adaptation service at all.
This decision does not touch `load_progress`/`load_adaptation` or the demo path in any way — only
scopes what Steps 9 (real Progress persistence) and 11 (real Adaptation triggering) inherit.

## Decision

**Reuse both services in the real per-user path**, per OQ-D. This step's code analysis confirms the
services themselves are sound — real `Protocol`-typed contracts (`ProgressAgent`, `AdapterAgent` in
`app/agents/contracts.py:60-86`), real `validate_agent_output` schema validation, and persistence
routed exclusively through `ProgressService`/`AdaptationService` (never a raw repository, respecting
`RULES.md` §5's agent/persistence boundary) — but it also found concrete defects that reuse must fix
first. These are named explicitly below so Steps 9/11 don't have to rediscover them.

### The ID-collision defect (confirmed, both services)

Both services mint their output record under a **hardcoded, unconditional canonical-demo ID**, not a
fresh or goal-scoped one:

- `app/agents/deterministic/progress.py:43` — `ProgressStateDTO(progress_state_id=demo.PROGRESS_ID, ...)`,
  regardless of which goal `build_progress_state()` is called for.
- `app/agents/services/adaptation.py:48` — `AdaptationEventDTO(adaptation_event_id=demo.ADAPTATION_ID, ...)`,
  regardless of which goal `plan()` is called for.

Traced concretely: both services persist via `create_or_get(create=..., get=..., record=...,
record_id=<the hardcoded id>)` (`app/agents/services/common.py:26-36`). `create()` on the underlying
store raises `DuplicateRecordError` the moment a record already exists under that ID
(`app/repositories/fakes/base.py:17-22`; the Mongo implementation enforces the same uniqueness).
`create_or_get` catches that and calls `get(record_id)` instead — **discarding the newly-built record
and returning whatever is already stored under the fixed ID.**

Concretely, if either service were wired into the real per-user path exactly as it stands today:
learner A calls `build()`/`plan()` first — their record is created under `progress_demo_rag` /
`adapt_demo_rag_retrieval`. Every subsequent learner B, C, D, ... who calls the same method gets a
`DuplicateRecordError` internally, which is swallowed, and the call returns **learner A's own progress
state / adaptation event** — silently, with no error surfaced. This is a genuine cross-user data
collision, not a demo-only quirk: **conclusion is a definitive yes**, this would leak one real
learner's data to every other real learner who ever calls the same method, until the process restarts
memory (fake backend) or forever (Mongo backend).

This is a small, well-understood, one-line-per-service fix, not a structural flaw: both repository
protocols already expose `list_by_goal_id()` (`app/repositories/protocols/progress.py:17`,
`app/repositories/protocols/adaptation.py:17`) — the exact lookup primitive
`WorkspaceGenerationService.generate()` already uses for knowledge-map/curriculum/critic/evaluation/quiz
IDs (`app/agents/services/workspace_generation.py:94-111`, via its `_new_id()` helper): mint a fresh ID
on first build for a goal, look up the existing one on regeneration. Reuse remains correct precisely
*because* the fix mirrors an already-established, working pattern in this codebase rather than
requiring new design.

### Other hardcoded canonical-demo dependencies found (beyond the ID collision)

`demo.NOW` used for `last_activity_at`/`created_at`/`updated_at` timestamps in both services is
cosmetic and not a concern. The following are real content/vocabulary leak risks, found while reading
both deterministic modules in full, and must be on Step 9/11's list even though this step does not fix
them:

- `app/agents/deterministic/progress.py:239-246` (`_concepts_for_topic`) — an **unconditional**
  fallback to `["rag_fundamentals"]` for any `topic_id` that doesn't contain "retrieval"/"vector"/
  "chunk" as a substring. Any non-RAG curriculum with a topic that crosses the stuck-count threshold
  will get `"rag_fundamentals"` injected into `stuck_events[].concept_ids` — a RAG-vocabulary leak of
  the same shape Rebuild-32/33/34 detoxed elsewhere and Step 6 guarded with `_RAG_TOKEN_PATTERN`.
- `app/agents/deterministic/adaptation.py:37` (`_weak_concepts`) — falls back to
  `["retrieval_evaluation"]` when no weak concepts are found from any real source (payload,
  quiz attempt, or progress state). This flows directly into `trigger_reason` and `expected_benefit`'s
  free text.
- `app/agents/deterministic/adaptation.py:75` (`_changes_for_concepts`) — falls back to
  `[demo.ADAPTATION_CHANGE.model_copy(deep=True)]`, an entire hardcoded canonical-demo
  `CurriculumChangeDTO`, when no real changes were computed for the weak concepts.
- `app/agents/deterministic/adaptation.py:84` (`_practice_topics`) — falls back to concept
  `"rag_fundamentals"` when a change carries no `affected_concept_ids` (a direct consequence of the
  previous fallback firing).
- `app/agents/deterministic/adaptation.py:99` (`_practice_topics`) — **every** generated practice
  topic is unconditionally stamped `adaptation_origin=demo.ADAPTATION_ID`, regardless of which real
  adaptation event produced it. This is not a fallback edge case — it is wrong on every single real
  call once a real, non-demo adaptation event ID exists.

`app/agents/deterministic/progress.py`'s `PRIORITY_WEAK_CONCEPTS` tuple and the `"rag_fundamentals" in
topic.concept_ids` branch in `_topic_progress` were checked and are **not** leaks — both are already
correctly gated on the curriculum's own concept IDs actually containing those values, the same
conditional pattern used elsewhere in the codebase.

## Explicitly Out Of Scope (this decision does not approve these)

- Building fresh parallel Progress/Adaptation implementations instead of reusing these services —
  ruled out per `RULES.md` §11 (avoid duplicating contracts that already exist and would drift), and
  because nothing found in this analysis rises to a structural flaw that would justify a rewrite.
- **Fixing the ID-collision defect, or any of the demo-shaped fallbacks listed above, in this step.**
  That is explicitly Step 9's job for Progress and Step 11's job for Adaptation
  (`RULES.md` §12 — no future-phase work pulled forward). No production code was changed to produce
  this decision record.
- Any change to `load_progress` / `load_adaptation` or the demo orchestration path's behavior — it
  must keep working exactly as it does today; this decision only scopes the *real per-user* path.

## Consequences

- **Step 9 (Progress)** must, at minimum: mint via `_new_id("progress")` on first build for a goal and
  look up the existing state via `list_by_goal_id()` on regeneration (mirroring
  `workspace_generation.py`'s established pattern), and gate `_concepts_for_topic`'s
  `"rag_fundamentals"` fallback the same way `curriculum.py`'s RAG-relevance gating already works —
  never unconditional.
- **Step 11 (Adaptation)** must, at minimum: mint via `_new_id("adaptation")` (or equivalent) on first
  plan for a goal and look up the existing event via `list_by_goal_id()` on re-planning; and either
  remove or properly gate the four demo-shaped fallbacks in `deterministic/adaptation.py` (weak-concept
  fallback, change fallback, practice-topic concept fallback, and the unconditional
  `adaptation_origin` stamp) so a real adaptation event never carries fixture-shaped content or a
  fixture-shaped provenance ID.
- Both Step 9 and Step 11 must **re-verify this defect list is still current** before building on it —
  this record is a snapshot as of 2026-07-22 against the code as it stood after Step 7; like every
  other document in this plan, it decays and must be checked against the real code, not trusted blind.
- No `RULES.md` exclusion is lifted or added by this decision; it is scoping guidance for two already-
  approved future steps, not an architecture change in itself.
