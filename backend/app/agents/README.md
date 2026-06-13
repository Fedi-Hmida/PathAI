# Agent Package

This package contains the Phase 3 LangGraph orchestration foundation.

Current scope:

- typed graph state,
- deterministic placeholder nodes,
- conditional routing,
- max revision control,
- failure routing,
- in-memory checkpointing,
- trace metadata,
- service wrapper for dev endpoints and future jobs.

Phase 3 intentionally does not implement real Assessor, Curriculum, Resource,
Critic, Adapter, RAG, authentication, production endpoints, or real LLM calls.

## P1 Service-Backed Local Demo Orchestration

P1 adds `app.agents.demo_orchestration.ServiceBackedDemoOrchestrator` and the
development endpoint:

```text
POST /api/v1/dev/graph/service-backed-demo-run
```

This path is different from the original placeholder graph demo. It coordinates
the implemented local services for:

1. assessment,
2. knowledge map finalization,
3. curriculum generation,
4. resource attachment,
5. critic review,
6. progress update,
7. quiz generation and scoring,
8. adapter/replanning,
9. synthetic evaluation.

It remains local-development only:

- no authentication,
- no production persistence,
- no real LLM requirement,
- no external network requirement,
- no Docker/deployment behavior.
