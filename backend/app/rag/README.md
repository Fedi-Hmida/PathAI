# Backend RAG Package

This package contains PathAI's Phase 6 Resource/RAG foundation. It validates
curated resource seeds, builds an in-memory catalog, retrieves resources for
curriculum topics, reranks candidates, attaches resources to curriculum
payloads, and exposes graph compatibility helpers.

## Canonical Resource Data Path

Curated resource seed data lives under:

```text
rag/resources/staging/
rag/resources/approved/
```

`data/resources/` is documentation-only compatibility. It is not a second source
of truth.

## Implemented Files

```text
backend/app/rag/__init__.py
backend/app/rag/constants.py
backend/app/rag/errors.py
backend/app/rag/schemas.py
backend/app/rag/resource_loader.py
backend/app/rag/curation.py
backend/app/rag/embeddings.py
backend/app/rag/vector_store.py
backend/app/rag/retriever.py
backend/app/rag/reranker.py
backend/app/rag/service.py
backend/app/rag/graph.py
backend/app/rag/README.md
```

## Resource Contract

Seed JSON files use external curation names:

```text
estimated_time_minutes
source
access_label
last_verified
```

The backend maps them into the internal resource contract:

```text
estimated_minutes
source_name
source_domain
access
last_verified_at
```

`source_domain` is derived from the seed URL hostname. This keeps the curated
seed files human-friendly while preserving a clean backend model boundary.

## Retrieval Behavior

The Phase 6 retriever is deterministic and offline-safe:

- topic token matching,
- subtopic token matching,
- difficulty-fit scoring,
- quality-score weighting,
- foundational-resource boost,
- open-access preference,
- token-overlap fallback,
- curated foundational fallback when no direct match exists.

The current implementation does not require ChromaDB, external search, real
embedding model downloads, or real LLM calls in tests.

## Reranking Behavior

The default reranker is deterministic. It prioritizes:

- match score,
- source quality,
- foundational status,
- accessibility,
- lightweight resource type diversity.

`rerank_with_mock_llm(...)` exercises the Phase 2 structured-output layer with
the mock LLM client and the `resource_rerank` prompt template. It does not call a
real LLM.

## Vector Boundary

`embeddings.py` and `vector_store.py` provide deterministic in-memory
abstractions for future vector search integration. They intentionally avoid
network calls and model downloads.

## API Surface

Temporary no-auth/demo endpoints:

```text
GET  /api/v1/resources/catalog/summary
POST /api/v1/resources/retrieve
POST /api/v1/resources/retrieve-for-curriculum
POST /api/v1/resources/validate-seed
GET  /api/v1/dev/resources/example
```

These endpoints must be protected or disabled before public deployment.

## Phase 6 Boundaries

Implemented:

- resource seed validation,
- curated seed loading from `rag/resources/`,
- in-memory catalog,
- deterministic retrieval,
- deterministic and mock-LLM reranking boundary,
- curriculum topic resource attachment,
- graph compatibility helpers,
- offline-safe tests.

Intentionally not implemented:

- Critic Agent,
- Adapter/replanning,
- authentication,
- production dashboard,
- real vector database,
- real web search fallback,
- real embedding model downloads,
- real-LLM-required tests.
