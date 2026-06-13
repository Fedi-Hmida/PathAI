# PathAI LLM Layer

This package contains the Phase 2 LLM infrastructure foundation.

It provides:

- async university LLM HTTP client,
- mock LLM client for tests and offline development,
- typed request/response models,
- structured JSON output parsing and Pydantic validation,
- safe LLM configuration serialization,
- lightweight redaction helpers.

Real provider calls are disabled by default with `LLM_MOCK_MODE=true`.
