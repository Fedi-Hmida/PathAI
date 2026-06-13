# Critic Package

This package contains the Phase 7 Critic Agent foundation.

The Critic is a quality gate after curriculum generation and resource
attachment. It reviews:

- curriculum structure,
- pacing and weekly hour limits,
- prerequisite and knowledge-map coverage,
- difficulty progression,
- resource coverage per topic,
- resource difficulty fit,
- resource type/source diversity,
- URL shape,
- `why_this` explanation quality.

## Current Behavior

The default path is deterministic and offline-safe. It does not call a real LLM,
does not require MongoDB, and does not require network access.

The mock-LLM path renders `critic_review.md`, redacts prompt content, calls the
Phase 2 `MockLLMClient`, and validates the structured response with Pydantic.

## API Routes

Temporary no-auth/demo endpoints:

```text
POST /api/v1/critic/review
POST /api/v1/critic/review-curriculum
GET  /api/v1/critic/rubric
GET  /api/v1/dev/critic/example
```

These routes must be protected or disabled before public deployment.

## Boundaries

Implemented:

- deterministic rubric,
- structured review output,
- approval/rejection decision,
- revision instructions,
- max-revision auto-approval metadata,
- graph-state compatibility helper.

Not implemented:

- Adapter/replanning,
- authentication,
- production persistence,
- LangSmith tracing,
- real-LLM-required tests,
- frontend Critic UI.
