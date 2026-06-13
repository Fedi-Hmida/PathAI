# Curriculum Package

Phase 5 implements the no-auth curriculum generation foundation for PathAI.

Current scope:

- curriculum request and result schemas,
- deterministic planner fallback,
- mock-LLM structured curriculum validation while `LLM_MOCK_MODE=true`,
- week-by-week curriculum generation,
- time budget and timeline validation,
- final project/application week,
- temporary no-auth API endpoints,
- in-memory curriculum store for offline-safe tests,
- graph-state compatibility helper.

Out of scope for Phase 5:

- authentication,
- Resource/RAG Agent,
- Critic Agent,
- Adapter/replanning,
- production dashboard,
- required real LLM calls,
- MongoDB-backed curriculum persistence in endpoint flow.
