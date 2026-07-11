# ADR-0001: JWT Authentication (Gate-Only) — Approved Exception To The No-Auth Rule

**Status:** Approved and implemented (Rebuild-25).
**Approved by:** Project owner, explicit request in-session (2026-07-11).

## Context

`docs/architecture/RULES.md` §7 and §15, and `docs/architecture/MAIN.md` §1
("Production concerns such as authentication ... remain intentionally
postponed"), establish PathAI as a local, no-auth demo. Authentication is
explicitly listed as excluded "unless the phase explicitly requests it."

The project owner explicitly requested JWT authentication, framed as a
deliberate, scoped exception rather than an ad hoc rule violation, per
`RULES.md` §2's requirement that any deviation from `MAIN.md`/`RULES.md` be
either compliant or an explicitly user-approved architecture update.

## Decision

Implement JWT authentication as a **gate**, not a full multi-tenant rework:

- Add a `User` concept (email + Argon2id-hashed password) and
  register/login/refresh/logout/me endpoints under `/api/v1/auth`.
- Short-lived access token held in the browser's memory only (never
  localStorage/sessionStorage, per `RULES.md` §10); long-lived refresh token
  in an httpOnly, Secure, SameSite cookie, with rotation and reuse detection.
- The entire feature is behind `PATHAI_ENABLE_AUTH` (default `false`). With
  the flag off, every existing route and the canonical no-auth demo behave
  exactly as before this phase — this decision does not retroactively change
  the demo's default posture.
- User and refresh-token persistence follow the existing repository pattern:
  a `UserRepository`/`RefreshTokenRepository` protocol, a fake in-memory
  implementation (default, keeps the deterministic test suite offline), and
  a MongoDB-backed implementation, wired through the existing
  `repositories/factory.py`.

## Explicitly Out Of Scope (this decision does not approve these)

- **Per-user data ownership.** Goals, runs, knowledge maps, etc. remain
  shared demo state even when a caller is authenticated. Scoping existing
  resources to their creating user is a distinct, separately-approved future
  phase.
- Role-based access control, admin panels, and production multi-user account
  management remain excluded per `RULES.md` §15, unchanged by this decision.

## Consequences

- `RULES.md` §15's blanket exclusion of "authentication / JWT / login /
  register / password hashing / user sessions / protected routes" no longer
  applies as a blanket rule — those are implemented, scoped as described
  above. `RULES.md` and `MAIN.md` carry short pointers to this record; see
  the diffs in the Rebuild-25 phase recap
  (`reports/phases/rebuild-25/Rebuild_25_JWT_Authentication_Gate_Result.md`).
- Per-user ownership, RBAC, and other `RULES.md` §15 items remain excluded
  until a future ADR explicitly approves them.
