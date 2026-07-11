# ADR-0002: Per-User Workspaces — Data Ownership And Isolation

**Status:** Approved and implemented (Rebuild-26).
**Approved by:** Project owner, explicit request in-session (2026-07-12).

## Context

After Rebuild-25 shipped gate-only JWT authentication, logging in changed nothing about
what data a user saw: every goal, run, knowledge map, curriculum, quiz, etc. was shared
demo state with no owner. The auth gate controlled *who could call the API*, never
*what a call returned* — flagged explicitly as "Not Done" in the Rebuild-25 recap and
called out again here by the project owner after trying it.

An audit confirmed the root cause: no schema carried a `user_id`; the frontend was
structurally single-tenant (`DEMO_RUN_ID` hardcoded); and the one seeding endpoint
(`POST /demo/load-fixtures`) wiped all data before reloading a single fixed demo graph.

## Decision

Give each authenticated user their **own isolated copy** of the workspace:

- **Ownership anchor**: `owner_user_id: UserId | None` added to `LearningGoalDTO` and
  `OrchestrationRunDTO` only. Every other artifact already carries a `goal_id`, so
  ownership is resolved transitively — no schema fan-out needed. `None` = shared/no-auth
  demo data, unchanged.
- **Read scoping**: a new `AuthorizationService` denies (404, not 403 — no existence
  leakage) any read whose resolved goal isn't owned by the caller. It is a no-op when
  auth is disabled, so the shared demo behaves exactly as before this phase.
- **Per-user seeding**: a generic, field-name-aware re-ID transform
  (`app/fixtures/workspace_factory.py`) clones the canonical demo content with fresh IDs
  per user, explicitly excluding shared reference data (the curated resource corpus,
  concept vocabulary). Reached through `POST /me/workspace` (explicit "Create my
  workspace"), `GET /me/workspace`, and `POST /me/workspace/reset` — all hidden unless
  auth is enabled.
- **Shared-state protection**: `POST /demo/load-fixtures` (which clears *all* data) is
  now hidden (404) while auth is enabled, since it would otherwise wipe every user's
  workspace.

## Explicitly Out Of Scope (this decision does not approve these)

- Uniquely-generated content per user (running the real LLM/agent pipeline from a
  user-entered goal into their workspace) — each user's starter content is currently a
  clone of the same canonical demo, not independently generated.
- Cascading deletion of orphaned artifacts on reset (the old goal/run are detached and
  become unreachable via authorization, but the underlying records are not swept).
- Role-based access control and other `RULES.md` §15 items not already lifted by
  ADR-0001.

## Consequences

- `RULES.md` §15's "per-user data ownership" exclusion is lifted for the gate-only shape
  described above; the recap under
  `reports/phases/rebuild-26/Rebuild_26_Per_User_Workspaces_Result.md` documents the
  change in detail.
- A real concurrency bug was found and fixed during implementation: on a fresh page
  load, a data-fetching page's request (fired before the session bootstrap has a token)
  and the auth bootstrap's own silent refresh both raced to call `/auth/refresh`
  independently; since refresh tokens rotate on use, the loser tripped reuse-detection
  and revoked the whole session. Fixed by deduping all concurrent refresh attempts into
  a single shared in-flight promise (`frontend/lib/api/client.ts`).
