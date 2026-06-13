# Security, Privacy, and Reliability Hardening

Phase 11 adds non-authentication hardening for local demos and future deployment.

Implemented controls:

- environment-based `/api/v1/dev/*` endpoint gating,
- environment-based temporary demo endpoint gating,
- CORS origin configuration,
- in-memory rate limiting for local/demo protection,
- request ID middleware,
- security response headers,
- audit event helpers with redacted metadata,
- shared redaction utilities for logs, prompts, and trace metadata,
- production-style internal error hiding.

Authentication is intentionally not implemented in this package. Do not add JWT, passwords, sessions,
register/login routes, or current-user ownership checks here. Those belong to a later authentication
phase.

## Local Defaults

Local/development/test environments keep dev and demo endpoints enabled by default.

Production-like environments disable dev and demo endpoints by default unless explicitly enabled.

## Public Demo Warning

Before exposing this API outside a controlled local environment:

- disable or protect `/api/v1/dev/*`,
- keep demo endpoints behind a controlled network or temporary access layer,
- restrict CORS origins,
- enable rate limiting,
- rotate local credentials,
- add authentication and user ownership checks in a later phase.
