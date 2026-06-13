# Adapter Package

This package contains the Phase 9 Adapter/Replanning foundation.

The Adapter inspects progress summaries and quiz history, detects adaptation
signals, and can run a deterministic manual replanning pipeline:

```text
Adapter -> Curriculum(replan affected weeks) -> Resource(refresh affected topics only) -> Critic -> Persist -> Notify
```

Current behavior is temporary and no-auth:

- signal detection is deterministic,
- replanning preserves completed weeks,
- affected weeks are regenerated or adjusted conservatively,
- resources are refreshed for affected topics when previous attachments exist,
- Critic review runs after replanning,
- persistence is an in-memory adaptation history,
- notification output is a payload only.

Not implemented:

- production scheduler,
- real email/SMS/push notification delivery,
- authentication and ownership checks,
- MongoDB persistence,
- production dashboard.
