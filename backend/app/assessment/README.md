# Assessment Package

Phase 4 implements the no-auth assessment foundation for PathAI.

Current scope:

- goal intake validation,
- assessment session state,
- deterministic question-bank fallback,
- mock-LLM structured question generation while `LLM_MOCK_MODE=true`,
- deterministic answer evaluation,
- adaptive difficulty updates,
- knowledge map generation,
- temporary no-auth API endpoints,
- in-memory store for offline-safe tests.

Out of scope for Phase 4:

- authentication,
- production user ownership checks,
- curriculum generation,
- RAG/resource retrieval,
- Critic review,
- Adapter/replanning,
- required real LLM calls.
