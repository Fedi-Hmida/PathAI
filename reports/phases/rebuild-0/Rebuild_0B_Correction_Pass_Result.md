> Canonical merged reference: `docs\architecture\MAIN.md`

# Rebuild-0B Correction Pass Result

Status: Completed  
Project: PathAI  
Phase: Rebuild-0B Correction Pass  

## A. Scope

This phase performed a focused correction pass on the Rebuild-0B Architecture, Contracts, and Roadmap specification document based on external reviews. The scope was strictly documentation and specification updates. No runtime logic, backend infrastructure, or frontend components were implemented.

## B. Reviews Incorporated

This pass incorporated critical reviews from external AI models (GLM, Gemini, Codex) and senior AI engineering best practices. The reviews verified that the architecture direction was sound but identified specific technical risks:
- `WorkflowState` bloat and checkpoint overhead.
- Frontend polling mechanics for long-running workflows.
- LLM structured-output reliability (specifically the University-hosted LLM).
- Progress synchronization after curriculum adaptations.

## C. Files Reviewed

Safe file reading was performed on the existing architecture specification to determine correct injection points.
- `docs/architecture/PathAI_Global_Architecture_And_Implementation_Blueprint.md`

The `.env` file was strictly avoided.

## D. Files Updated

**Updated:**
- `docs/architecture/PathAI_Global_Architecture_And_Implementation_Blueprint.md`

**Created:**
- `reports/phases/Rebuild_0B_Correction_Pass_Result.md`

## E. Main Corrections Added

The following core architectural corrections and enhancements were integrated:
1. **Execution Modes Defined:** Clear distinction between `Interactive Mode` and `Deterministic Demo Mode`.
2. **Lightweight Workflow State:** Redesigned `WorkflowState` to store string IDs and summaries rather than full nested Pydantic documents, preventing graph state bloat.
3. **Orchestration Polling:** Replaced blocking HTTP POST assumptions with a robust `/api/v1/orchestration/runs/{run_id}/status` polling contract.
4. **LLM Structured Output Spike:** Adjusted the roadmap (Rebuild-1) to prioritize a spike confirming the University-hosted LLM can successfully return complex JSON schemas before committing to them.
5. **Idempotency & Naming Conventions:** Defined strict ID prefixes (e.g., `goal_`, `run_`) and established explicit idempotency rules for API routes and workflow retries.
6. **Curriculum Versioning & Progress Sync:** Formalized how adaptation creates a new curriculum revision, preserving `TopicProgress` for untouched topics and updating the `ProgressState` differential.
7. **Seed Corpus Acceptance Standard:** Added a rigorous acceptance criteria for RAG v1 (minimum 40-60 curated resources, specific fields, and diversity markers) and explicitly categorized embeddings as a v2 enhancement.
8. **Dashboard Payload Schema:** Introduced a frontend-friendly read-model schema (`DashboardPayload`) mapped by the DashboardService.
9. **Observability Rules:** Mandated `request_id`/`run_id` trace propagation, structured logging per workflow node, and safe frontend error handling.
10. **Evaluation Tuning:** Refined the Quiz Alignment metric to specifically check alignment against weak concepts in the knowledge map.
11. **Roadmap Restructuring:** Merged the Mock LLM fixtures with the Core Schemas phase to validate schemas immediately.

## F. Remaining Open Questions

- Does the University-hosted LLM support a strict JSON mode/function calling capability, or will it require a heavy LLM parser/repair pipeline? (To be tested in Rebuild-1).
- Should the `POST /api/v1/orchestration/runs/{run_id}/cancel` endpoint be prioritized for the local demo, or safely deferred until a later production phase?

## G. Validation Performed

Validation was documentation-based:
- Validated injection of all required 25 correction points into the architecture document.
- Safely searched and updated the markdown document using programmatic text replacement without corrupting surrounding sections.
- Verified file creation and correct path structure.

## H. Not Done

The following were intentionally NOT done, adhering strictly to scope:
- No backend runtime logic was implemented.
- No frontend runtime logic was implemented.
- No dependencies (`npm install` / `pip install`) were executed.
- No authentication or deployment infrastructure (Docker, CI/CD) was implemented.
- The `.env` file was not read, printed, copied, modified, or exposed.

## I. Next Recommended Phase

**Rebuild-1: Backend Project Foundation, Tooling, And LLM Spike**

The architecture contracts are now implementation-ready. The next phase will establish the FastAPI application skeleton, testing foundation, and explicitly test the University-hosted LLM's capacity for complex JSON output. No product business logic should be written until Rebuild-2 schemas and Mock fixtures are in place.


