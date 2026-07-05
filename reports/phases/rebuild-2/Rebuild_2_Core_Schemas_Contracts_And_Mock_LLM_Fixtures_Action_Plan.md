# Rebuild-2 Core Schemas, Contracts, And Mock LLM Fixtures Action Plan

Status: Action plan  
Project: PathAI  
Phase: Rebuild-2  
Created: 2026-07-05  

## A. Phase Objective

Rebuild-2 converts the architecture contracts in `docs\architecture\MAIN.md` into concrete backend Pydantic schema modules and deterministic mock fixture data.

The purpose is to make PathAI's core data contracts explicit, typed, reusable, and testable before implementing fake repositories, services, API routes, MongoDB persistence, LangGraph orchestration, frontend consumption, or product workflows.

Rebuild-2 should produce:

- Product DTO schemas for the local no-auth demo contract surface.
- Shared ID, timestamp, version, and status primitives.
- Agent input/output schemas needed for structured-output validation.
- Lightweight orchestration state schemas.
- Dashboard payload read-model schemas.
- Deterministic canonical demo fixtures.
- Deterministic mock agent/LLM output fixtures.
- Schema and fixture validation tests that do not require network, MongoDB, or live LLM calls.

Rebuild-2 should not run the PathAI learning pipeline. It is a contract and fixture foundation phase only.

## Roadmap Alignment Note

This action plan intentionally combined the canonical `Rebuild-2: Core Schemas And Contracts` scope with the mock-fixture scope listed in `docs\architecture\MAIN.md` as `Rebuild-3: Mock LLM And Deterministic Agent Fixtures`.

Because this plan included deterministic mock agent/LLM fixtures, future phases should continue from the canonical roadmap numbering in `MAIN.md`.

The next canonical implementation phase after this combined result should be:

```text
Rebuild-4: Fake Repositories And Service Skeleton
```

## B. MAIN.md / RULES.md Alignment

This phase is governed by the following architecture and rulebook requirements:

- Use typed contracts and explicit DTOs.
- Keep schema files small, cohesive, and separated by domain.
- Avoid giant files and catch-all utility modules.
- Keep schemas, services, repositories, agents, orchestration, API routes, and tests separated.
- Do not put business logic in schemas or API routes.
- Do not put persistence logic inside agents or schemas.
- Treat LLM outputs as untrusted data.
- Validate all agent and mock LLM outputs with Pydantic before later persistence or display.
- Use mock-first behavior and deterministic fixtures.
- Default tests must not require real LLM calls, network access, MongoDB, Docker, frontend, or secrets.
- Do not implement services, repositories, MongoDB models, LangGraph execution, API routes beyond existing health/readiness, frontend code, authentication, Docker, or deployment.
- Preserve `.env`; never read, print, copy, modify, or expose it.
- Keep `.env.example` placeholder-only.
- Keep the no-auth local demo scope explicit and avoid future-phase implementation.
- Create a phase result recap under `reports\phases`.

## C. Current Starting Point

After Rebuild-1B:

- Backend foundation exists under `backend\app`.
- FastAPI app factory, health endpoint, readiness endpoint, settings layer, logging foundation, and LLM spike scaffold exist.
- Backend dependencies have been installed in a local virtual environment by the user.
- Validation is green:
  - `compileall` passed.
  - `pytest` passed with default live LLM tests skipped.
  - `ruff` passed.
  - `mypy` passed.
- Mock LLM structured-output spike exists.
- `backend\app\schemas` currently contains the Rebuild-1 spike schema file `llm_spike.py`, plus package files.
- Live LLM was not used in Rebuild-1B.
- No product contracts, domain schemas, fake repositories, services, product API routes, MongoDB persistence, LangGraph workflow, or frontend implementation exist yet.

## D. In Scope

Allowed Rebuild-2 work:

- Core shared schema primitives.
- ID prefix contracts and ID validation helpers.
- Base DTOs for timestamps, schema versions, run metadata, warnings, and errors.
- Status enums and controlled vocabularies.
- Goal and learner profile schemas.
- Assessment session, question, answer, score, and concept evidence schemas.
- Knowledge map and concept mastery schemas.
- Curriculum, week, topic, outcome, and curriculum-change schemas.
- Resource corpus and resource attachment schemas.
- Progress state, topic progress, stuck event, and recommendation schemas.
- Quiz, quiz question, scoring policy, quiz answer, quiz attempt, and concept score schemas.
- Adaptation event and replanning output schemas.
- Critic review schemas.
- Evaluation report schemas.
- Lightweight orchestration state, node event, workflow error, and workflow warning schemas.
- Dashboard payload read-model schema.
- Deterministic mock LLM/agent output fixtures.
- Canonical demo fixture data aligned with `MAIN.md`.
- Schema import tests.
- Schema validation tests.
- Fixture validation tests.
- Mock agent fixture validation tests.
- Security tests for secret-like strings in fixtures.
- Documentation/README updates only if needed for schema usage.
- Rebuild-2 result recap under `reports\phases\rebuild-2`.

## E. Out Of Scope

Explicitly excluded from Rebuild-2:

- Business services.
- Repository interfaces or implementations.
- API routes beyond existing health/readiness.
- MongoDB document models or persistence.
- MongoDB connections or integration tests.
- LangGraph graph execution or node implementation.
- Real LLM calls.
- Live LLM adapter changes.
- RAG ranking implementation.
- Resource retrieval algorithms.
- Quiz scoring implementation.
- Adaptation execution.
- Progress mutation logic.
- Evaluation scoring implementation.
- Frontend code.
- Authentication, JWT, login/register, password hashing, sessions, or protected routes.
- Docker.
- Deployment.
- CI/CD.
- Production hosting.
- Live web scraping.

## F. Proposed Schema Module Structure

Create small separated modules under `backend\app\schemas`. Avoid one large schema file.

### `backend\app\schemas\base.py`

Responsibility:

- Shared schema primitives used across domains.

Examples:

- `TimestampedDTO`
- `VersionedDTO`
- `WorkflowError`
- `WorkflowWarning`
- `TraceMetadata`
- common constrained score aliases if useful

Rules:

- Keep generic only.
- Do not include domain-specific model fields.

### `backend\app\schemas\ids.py`

Responsibility:

- Opaque string ID validation and ID prefix constants.

Examples:

- `GoalId`
- `RunId`
- `AssessmentId`
- `AnswerId`
- `KnowledgeMapId`
- `CurriculumId`
- `WeekId`
- `TopicId`
- `ResourceId`
- `AttachmentId`
- `ProgressId`
- `QuizId`
- `QuestionId`
- `AttemptId`
- `AdaptationId`
- `CriticReviewId`
- `EvaluationReportId`

Rules:

- Validate prefixes from `MAIN.md`.
- Do not generate IDs in schemas unless a later phase explicitly chooses a generator utility.
- Do not assume MongoDB ObjectId.

### `backend\app\schemas\enums.py`

Responsibility:

- Shared enums and controlled vocabularies.

Examples:

- `DifficultyLevel`
- `ExecutionMode`
- `GoalStatus`
- `AssessmentStatus`
- `KnowledgeMapStatus`
- `CurriculumStatus`
- `ResourceStatus`
- `ResourceType`
- `ProgressStatus`
- `TopicProgressStatus`
- `QuizStatus`
- `QuizAttemptStatus`
- `AdaptationStatus`
- `CriticPassStatus`
- `EvaluationPassStatus`
- `OrchestrationStatus`
- `NodeResultStatus`
- `ConceptClassification`

Rules:

- Keep enums stable and string-valued.
- Prefer values already defined in `MAIN.md`.

### `backend\app\schemas\goal.py`

Responsibility:

- Learning goal and learner profile contracts.

Examples:

- `LearnerProfile`
- `LearningGoalBase`
- `LearningGoalCreate`
- `LearningGoalDTO`
- `LearningGoalSummary`

Key constraints:

- Goal text has minimum and maximum length.
- Learner profile fields are optional but explicit.
- No authentication or user-account fields.

### `backend\app\schemas\assessment.py`

Responsibility:

- Diagnostic assessment contracts.

Examples:

- `AssessmentQuestionDTO`
- `AssessmentAnswerDTO`
- `AssessmentAnswerCreate`
- `AssessmentSessionDTO`
- `ConceptEvidence`
- `ConceptEvidenceUpdate`
- `AssessmentAgentInput`
- `AssessmentAgentOutput`
- `AssessmentScoreOutput`

Key constraints:

- Question types controlled by enum.
- Scores normalized between `0.0` and `1.0`.
- Target concepts must not be empty.

### `backend\app\schemas\knowledge_map.py`

Responsibility:

- Knowledge map and concept mastery contracts.

Examples:

- `ConceptMasteryDTO`
- `KnowledgeMapDTO`
- `KnowledgeMapCreate`
- `KnowledgeMapAgentInput`
- `KnowledgeMapAgentOutput`

Key constraints:

- At least one concept.
- Mastery scores normalized between `0.0` and `1.0`.
- Classification must use `ConceptClassification`.

### `backend\app\schemas\curriculum.py`

Responsibility:

- Curriculum, week, topic, and curriculum change contracts.

Examples:

- `CurriculumTopicDTO`
- `CurriculumWeekDTO`
- `CurriculumDTO`
- `CurriculumCreate`
- `CurriculumChangeDTO`
- `CurriculumAgentInput`
- `CurriculumAgentOutput`

Key constraints:

- Duration matches week count where practical.
- Topics include concept IDs.
- Difficulty uses `DifficultyLevel`.
- Versioning fields are present where needed: `version`, `parent_curriculum_id`, `revision_reason`.

### `backend\app\schemas\resource.py`

Responsibility:

- Curated resource corpus and attachment contracts.

Examples:

- `ResourceDTO`
- `ResourceSeedItem`
- `ResourceAttachmentDTO`
- `ResourceCoverageSummary`
- `ResourceFilter`
- `ResourceAgentInput`
- `ResourceAgentOutput`

Key constraints:

- Relevance, quality, freshness, and diversity scores normalized between `0.0` and `1.0`.
- Resource type uses allowed enum values.
- Public URLs are allowed only as non-secret resource metadata.

### `backend\app\schemas\progress.py`

Responsibility:

- Learner progress contracts.

Examples:

- `TopicProgressDTO`
- `StuckEventDTO`
- `ProgressStateDTO`
- `ProgressStateCreate`
- `NextRecommendedAction`

Key constraints:

- Completion normalized between `0.0` and `1.0`.
- Topic progress status uses enum.
- Stuck events reference goal/topic IDs.

### `backend\app\schemas\quiz.py`

Responsibility:

- Quiz generation, learner-safe quiz display, answers, scoring policy, and attempts.

Examples:

- `QuizQuestionDTO`
- `QuizScoringPolicy`
- `QuizDTO`
- `LearnerQuizDTO`
- `QuizAnswerSubmission`
- `QuizAttemptDTO`
- `ConceptQuizScore`
- `QuizAgentInput`
- `QuizAgentOutput`
- `QuizScoreOutput`

Key constraints:

- Every question maps to concept IDs.
- Answer keys should not be part of learner-facing quiz DTOs.
- Scores normalized between `0.0` and `1.0`.

### `backend\app\schemas\adaptation.py`

Responsibility:

- Adapter/replanning contracts and stored adaptation event shape.

Examples:

- `AdaptationEventDTO`
- `AdaptationTrigger`
- `AdaptationAgentInput`
- `AdaptationAgentOutput`
- `CurriculumChangeDTO` import or shared ownership decision with `curriculum.py`

Key constraints:

- Before/after summary required.
- Changes must be bounded and reference affected concepts/topics.
- No destructive whole-curriculum deletion contract.

### `backend\app\schemas\critic.py`

Responsibility:

- Critic review contracts.

Examples:

- `CriticReviewDTO`
- `CriticAgentInput`
- `CriticAgentOutput`
- `CriticDimensionScores`

Key constraints:

- Overall and dimension scores normalized between `0.0` and `1.0`.
- Pass status uses `pass`, `revise`, or `pass_with_warnings`.
- Revision recommendations are structured strings, not free-form persistence commands.

### `backend\app\schemas\evaluation.py`

Responsibility:

- Evaluation report contracts.

Examples:

- `EvaluationReportDTO`
- `EvaluationMetricScores`
- `EvaluationAgentInput`
- `EvaluationAgentOutput`

Key constraints:

- Weighted score normalized between `0.0` and `1.0`.
- Pass status follows evaluation enum.
- Warnings and recommendations are explicit lists.

### `backend\app\schemas\orchestration.py`

Responsibility:

- Lightweight workflow state and orchestration event contracts.

Examples:

- `WorkflowState`
- `WorkflowNodeEvent`
- `OrchestrationRunDTO`
- `OrchestrationRunCreate`
- `OrchestrationStatusResponse`

Key constraints:

- Store IDs, statuses, counters, warnings, and errors.
- Do not store giant nested full documents in workflow state.
- Do not implement graph behavior.

### `backend\app\schemas\dashboard.py`

Responsibility:

- Command center read-model DTOs.

Examples:

- `DashboardPayload`
- `RunSummary`
- `GoalSummary`
- `KnowledgeMapSummary`
- `CurriculumSummary`
- `ProgressSummary`
- `QuizSummary`
- `ResourcesSummary`
- `AdaptationSummary`
- `EvaluationSummary`
- `DashboardUIFlags`

Key constraints:

- Dashboard schema composes summaries only.
- It does not replace canonical stored documents.
- It does not mutate state or call services.

### `backend\app\schemas\llm_spike.py`

Responsibility:

- Keep existing Rebuild-1 LLM spike schemas while they remain useful.

Rules:

- Do not mix spike-only schemas with product contracts unless intentionally migrated.
- If migrated later, preserve tests or add compatibility notes.

## G. Core Contract Rules

Schema implementation rules:

- Use Pydantic v2 models and validators.
- Use explicit field names aligned with `MAIN.md`.
- Use clear validation constraints for required fields, lengths, scores, counts, statuses, and IDs.
- Use string-valued enums for stable JSON payloads.
- Use consistent timestamp fields: `created_at`, `updated_at`, `completed_at`, `started_at`, and `submitted_at` where applicable.
- Use `schema_version` on persisted-artifact DTOs where relevant.
- Use opaque backend IDs and prefix validation.
- Do not import database drivers.
- Do not import service, repository, route, or LangGraph execution modules into schemas.
- Do not include agent prompt text in schema modules.
- Do not include persistence logic.
- Do not include frontend-only behavior.
- Keep optional fields justified by the architecture contract.
- Treat LLM and fixture output as untrusted until validated by schemas.
- Keep examples and fixture data free of secrets and real user data.
- Prefer model-level validators only for structural contract checks, not business workflow decisions.

## H. ID And Status Strategy

ID handling:

- All API/domain IDs are opaque URL-safe strings.
- IDs must not assume MongoDB `ObjectId`.
- Prefixes come from `MAIN.md`:
  - `goal_`
  - `run_`
  - `assessment_`
  - `answer_`
  - `kmap_`
  - `curriculum_`
  - `week_`
  - `topic_`
  - `resource_`
  - `attach_`
  - `progress_`
  - `quiz_`
  - `question_`
  - `attempt_`
  - `adapt_`
  - `critic_`
  - `eval_`

Recommended implementation:

- Define reusable prefix constants in `ids.py`.
- Define small constrained ID types or validation helpers per ID category.
- Use the domain-specific ID aliases in all schemas.
- Validate prefix and basic URL-safe shape.

Status enum plan:

- Goal status: `created`, `assessment_started`, `curriculum_generated`, `active`, `completed`, `failed`.
- Assessment status: `created`, `in_progress`, `completed`, `failed`.
- Knowledge map status: `draft`, `active`, `superseded`, `failed`.
- Orchestration status: `queued`, `running`, `waiting_for_user`, `completed`, `failed`, `cancelled`.
- Orchestration run document status: `created`, `in_progress`, `requires_input`, `completed`, `completed_with_warnings`, `failed`.
- Curriculum status: `draft`, `under_review`, `active`, `adapted`, `superseded`, `failed`.
- Resource status: `active`, `deprecated`, `needs_review`.
- Resource attachment status: `active`, `superseded`, `removed`.
- Progress status: `not_started`, `in_progress`, `adaptation_needed`, `completed`.
- Topic progress status: `not_started`, `in_progress`, `completed`, `stuck`, `needs_review`.
- Quiz status: `draft`, `active`, `completed`, `archived`.
- Quiz attempt status: `submitted`, `scored`, `failed`.
- Adaptation status: `proposed`, `applied`, `failed`.
- Critic pass status: `pass`, `revise`, `pass_with_warnings`, `failed`.
- Evaluation pass status: `pass`, `fail`, `pass_with_warnings`.
- Node result status: `success`, `failed`, `skipped`, `requires_input`.

## I. Mock LLM Fixtures Plan

Create deterministic mock outputs for:

- Assessment Agent.
- Knowledge Map Agent.
- Curriculum Agent.
- Resource/RAG Agent.
- Critic Agent.
- Quiz Agent.
- Adapter/Replanning Agent.
- Evaluation Agent.

Fixture rules:

- Fixtures must live separately from schema definitions.
- Fixtures must validate against Rebuild-2 product schemas.
- Fixtures must align with the canonical demo goal.
- Fixtures must not call a real LLM.
- Fixtures must not require network access.
- Fixtures must not require MongoDB.
- Fixtures must not contain secrets, private config, API keys, tokens, credentials, or real user data.
- Fixtures should be deterministic and stable for tests.

Recommended location:

- Use `backend\app\fixtures` for valid canonical demo and mock agent fixtures.
- Use `backend\app\tests\fixtures` only for intentionally invalid or test-only payloads.

Reason:

- Valid canonical fixtures should be reusable by tests, later fake repositories, later mock agents, and deterministic demo mode without importing from test modules into application code.
- Keeping invalid cases under tests prevents production modules from carrying deliberately malformed examples.

Suggested fixture files for future implementation:

- `backend\app\fixtures\canonical_demo.py`
- `backend\app\fixtures\mock_agents.py`
- `backend\app\tests\fixtures\invalid_payloads.py` if needed

Fixtures should be plain data builders or constants. They should not run workflows or make decisions.

## J. Canonical Demo Dataset Plan

The deterministic demo dataset should include:

- Goal:
  - `Learn RAG systems for an AI engineering graduation project`
- Learner profile:
  - final-year AI engineering student.
  - Python basics.
  - general machine learning familiarity.
  - basic web API knowledge.
  - weak areas in vector search, chunking, retrieval metrics, embedding evaluation, and production RAG failure modes.
  - 6 to 8 hours per week.
  - intermediate difficulty target.
- Assessment questions:
  - 5 to 8 deterministic questions.
  - Mix of multiple-choice, short-answer, and self-rating.
  - Concepts include RAG fundamentals, embeddings, chunking, vector databases, retrieval ranking, prompt augmentation, hallucination reduction, evaluation metrics, system design, and FastAPI integration.
- Assessment answers:
  - Seeded answers that show strengths in Python/API basics and high-level RAG.
  - Seeded weak evidence for retrieval evaluation, chunking, vector search, and production RAG failure modes.
- Expected knowledge map:
  - strong concepts: Python basics, API basics, high-level RAG fundamentals.
  - developing concepts: chunking, embeddings, prompt augmentation.
  - weak concepts: retrieval evaluation, vector search, hallucination reduction.
  - missing concepts: reranking, production failure modes, evaluation metrics.
- Expected curriculum outline:
  - 4 weeks.
  - 2 to 4 topics per week.
  - topics reference concept IDs.
  - includes project-oriented tasks.
- Expected resources:
  - curated non-secret public or placeholder resources.
  - resource types include documentation, tutorial, paper, article, video, code/lab, exercise, and checklist where available.
  - resource attachments include relevance and selection reason.
- Expected quiz:
  - 5 to 8 questions.
  - focuses on weak or newly taught concepts.
  - includes concept mapping and answer key in backend-only DTOs.
- Expected quiz attempt:
  - deterministic low score below adaptation threshold.
  - weak concepts include retrieval evaluation and vector search.
- Expected adaptation event:
  - trigger reason: quiz score below threshold.
  - inserts remedial retrieval metrics practice.
  - preserves prior curriculum history.
- Expected evaluation report:
  - deterministic metric scores.
  - overall pass score at or above `0.80` for the completed canonical demo path.
  - warnings are explicit if fixture data is intentionally simplified.

## K. Testing Plan For Rebuild-2

Planned tests:

### `backend\app\tests\test_schema_imports.py`

- Import every new schema module.
- Assert product schemas can be imported without importing services, repositories, MongoDB, LangGraph, or API routes.

### `backend\app\tests\test_schema_validation.py`

- Validate representative valid payloads for each domain.
- Reject invalid enum/status values.
- Reject invalid scores outside `0.0` to `1.0`.
- Reject empty required lists where the contract requires data.
- Reject invalid ID prefixes if prefix validation is implemented.

### `backend\app\tests\test_demo_fixtures_validate.py`

- Validate canonical demo goal fixture.
- Validate learner profile fixture.
- Validate assessment, knowledge map, curriculum, resources, quiz, adaptation, and evaluation fixtures.
- Confirm fixture IDs consistently link to each other.

### `backend\app\tests\test_mock_agent_fixtures_validate.py`

- Validate deterministic mock agent outputs against their agent output schemas.
- Confirm fixture outputs align with the canonical demo goal.
- Confirm no real LLM client is called.

### `backend\app\tests\test_schema_security.py`

- Scan fixture string values for secret-like markers.
- Assert no fixture contains API keys, tokens, passwords, MongoDB connection strings, `.env` content, or private credentials.
- Assert fixture modules do not read environment files.

### Additional dashboard validation

- Validate `DashboardPayload`.
- Confirm dashboard summaries reference IDs and summaries, not giant nested full artifacts.

Default tests must not require:

- live LLM calls.
- network.
- MongoDB.
- Docker.
- frontend.
- secrets.

## L. Validation Commands

After Rebuild-2 implementation, run from `C:\Users\Fedi\Desktop\PathAI\backend`:

```cmd
python -m compileall app
python -m pytest
python -m ruff check app
python -m mypy app --no-incremental
```

Validation expectations:

- All schema and fixture tests pass.
- Existing live LLM tests remain skipped by default.
- No MongoDB tests are added or required.
- No frontend tests are run.
- No network-dependent tests are run.

Optional explicit live-skip check may be run only to confirm skip behavior, without enabling live tests:

```cmd
python -m pytest app\tests\test_live_llm_spike_optional.py -v
```

## M. File Size And Modularity Rules

Implementation must follow these rules:

- No huge schema files.
- Split schemas by domain.
- Keep shared primitives in `base.py`, `ids.py`, and `enums.py` only when genuinely common.
- Avoid circular imports.
- Prefer domain modules importing shared primitives, not importing each other heavily.
- Use forward references only when unavoidable.
- Keep fixtures separated from schemas.
- Keep tests separated by concern.
- Keep LLM spike schemas separate from product schemas unless there is an explicit migration decision.
- Do not duplicate contracts across unrelated files.
- Avoid schema modules becoming business-service modules.
- Avoid generated code or broad mechanical churn.

## N. Security Checklist

Rebuild-2 implementation must satisfy:

- Do not read, print, copy, modify, or expose `.env`.
- Do not add secrets to schemas, fixtures, tests, docs, or README files.
- Do not include API keys, tokens, passwords, private keys, MongoDB URIs, or credentials.
- Do not include real user data.
- Public resource URLs are acceptable only when non-secret and intentionally curated.
- Do not include raw provider errors.
- Do not call a live LLM.
- Do not enable `ENABLE_LIVE_LLM_TESTS`.
- Do not require network access.
- Do not require MongoDB.
- Do not add frontend-visible secrets.
- Keep all examples and fixtures safe for local demo and academic review.

## O. Done Criteria

Rebuild-2 is complete only when:

- Planned schema modules exist and stay focused by domain.
- Shared base, ID, and enum contracts exist.
- Product agent input/output schemas exist.
- Dashboard payload schema exists.
- Canonical demo fixtures exist.
- Mock agent/LLM fixtures exist.
- Fixtures validate against schemas.
- Schema security tests pass.
- Default tests pass without network, MongoDB, live LLM, Docker, frontend, or secrets.
- `compileall`, `pytest`, `ruff`, and `mypy` pass.
- Existing live LLM tests remain skipped by default.
- No business services are implemented.
- No repositories are implemented.
- No MongoDB persistence is implemented.
- No LangGraph execution is implemented.
- No new product API routes are implemented.
- No frontend work is implemented.
- No `.env` access occurs.
- Rebuild-2 result recap is created.

## P. Risks And Mitigations

| Risk | Impact | Mitigation |
|---|---:|---|
| Schema files become too large | Medium | Split by domain and extract only genuinely shared primitives. |
| Over-modeling too early | Medium | Model contracts needed by `MAIN.md`; avoid speculative production-only fields. |
| Under-modeling contracts | High | Cover all major artifacts needed by later repositories, services, orchestration, and dashboard. |
| Circular imports | Medium | Keep common enums/IDs/base in shared modules and avoid domain cross-dependencies where possible. |
| Fixtures drift from schemas | High | Add fixture validation tests that instantiate Pydantic models. |
| Accidentally implementing business logic | High | Limit validators to structural checks; postpone workflow decisions to services/orchestration phases. |
| Mock data does not match canonical journey | High | Tie fixtures to the canonical RAG graduation-project goal from `MAIN.md`. |
| Mypy complexity | Medium | Prefer simple Pydantic models and explicit imports; avoid dynamic model construction. |
| Validation constraints too strict | Medium | Use constraints from `MAIN.md`; keep optional fields where future phases need incomplete workflow states. |
| Validation constraints too loose | Medium | Reject malformed IDs, invalid statuses, empty required lists, and out-of-range scores. |
| Secret-like fixture strings | High | Add security test scanning fixture string values. |

## Q. Required Rebuild-2 Result Recap Structure

Implementation must create:

```text
C:\Users\Fedi\Desktop\PathAI\reports\phases\rebuild-2\Rebuild_2_Core_Schemas_Contracts_And_Mock_LLM_Fixtures_Result.md
```

The recap must include:

```text
A. Scope
B. MAIN.md / RULES.md Compliance
C. Files Created or Updated
D. Work Completed
E. Validation Commands And Results
F. Security / Secret Handling
G. Mock LLM / Fixture Result
H. Not Done / Intentionally Postponed
I. Remaining Risks
J. Next Recommended Phase
```

The recap must report exact validation command outcomes and honestly record warnings, skipped tests, and any limitations.

## R. Recommended Implementation Sequence

Future implementation should proceed in this order:

1. Re-read `docs\architecture\MAIN.md` and `docs\architecture\RULES.md`.
2. Inspect existing `backend\app\schemas` and Rebuild-1 LLM spike files.
3. Create shared `base.py`, `ids.py`, and `enums.py`.
4. Create domain schema files for goal, assessment, knowledge map, curriculum, resource, progress, quiz, adaptation, critic, evaluation, orchestration, and dashboard.
5. Create canonical demo fixtures.
6. Create mock agent/LLM fixtures.
7. Add schema import, validation, fixture validation, mock fixture validation, dashboard validation, and schema security tests.
8. Run validation commands.
9. Fix only schema, fixture, typing, lint, or test issues within Rebuild-2 scope.
10. Create the Rebuild-2 result recap with exact validation results.

Do not implement services, repositories, API routes, MongoDB, LangGraph, frontend, auth, Docker, deployment, or live LLM calls during any step.

## S. Final Recommendation

Rebuild-2 implementation should begin after this action plan is approved.

The implementation should stay tightly scoped to typed contracts, deterministic fixtures, and validation tests. It should not run or implement the PathAI learning workflow yet.
