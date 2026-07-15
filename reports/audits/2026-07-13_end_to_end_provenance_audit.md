# PathAI End-to-End Provenance Audit — 2026-07-13

Scope: full user journey (login → workspace → live diagnostic → generate → dashboard and
sub-screens). Goal: every user-visible field must be REAL per-user AI/user data, zero
mock/demo-clone/cross-topic-fallback content. All claims below are backed by `file:line`,
a live gateway response, or a config value observed this session. Secrets were never
printed; the LLM key/host were redacted in every command.

---

## A. Executive summary

- **The reported symptom ("goal = NLP, but diagnostic/knowledge-map/dashboard show RAG") is real and reproducible, but the prior phase reports mis-diagnosed the cause.** They claimed "the LLM gateway is timing out on every request" as an external outage. It is **not** an outage: the gateway is reachable (TCP+TLS in ~140 ms, `GET /models` → HTTP 401 in 0.4 s) and answers `POST /api/chat/completions` — it returns **HTTP 400 `{"detail":"404: Model not found"}`** because the configured model id `hosted_vllm/Llama-3.1-70B-Instruct` is wrong (that `hosted_vllm/` prefix is a server-side LiteLLM routing prefix, not a client-facing model id). This is a **configuration bug**, not an infrastructure failure.
- **Even a perfectly working gateway would still serve a RAG diagnostic**, because the user's `.env` only enables `PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT=true`. The assessment and curriculum LLM agents are **disabled**, so those stages run the deterministic path regardless of gateway health.
- **The deterministic assessment path can only ever ask 5 hardcoded RAG questions.** `_select_question` (`app/agents/deterministic/assessment.py:309`) iterates only `demo.ASSESSMENT_QUESTIONS`, and when the goal keywords don't match (they never will, for NLP) it falls through to returning those same RAG questions in order. Question #1 is verbatim the one the owner saw: *"Which component finds relevant documents in a RAG pipeline?"* (`canonical_demo.py:119`).
- **Every LLM agent silently falls back to RAG-seeded deterministic output** via `fallback_on_error=True` (`activation/factory.py:78–145`). So the one enabled LLM agent (knowledge map) also produces RAG content once its call 400s. This is the mechanism that turns a config bug into cross-topic content — and it directly violates the owner's "fail loud, never show another topic's material" rule.
- **Six of the eight dashboard artifacts are never regenerated from the user's assessment.** Workspace creation clones all 11 artifacts from the single canonical RAG demo (`workspace_factory.py:127–139`); `POST /me/workspace/generate` only rebuilds knowledge map + curriculum (`workspace_generation.py:58–68`). Quiz, critic review, evaluation report, progress, adaptation, and resources remain RAG demo-clones on the dashboard forever.
- **The assessment scorer poisons everything downstream even when it "works".** The deterministic scorer keys off RAG question ids and emits RAG concept-evidence (`assessment.py:70–146`); that evidence is what feeds the knowledge-map and curriculum agents. So the LLM knowledge map, even if its call succeeded, would be prompted with RAG evidence.
- **One-sentence answer for the owner:** *NLP shows RAG because the diagnostic's AI is switched off (only the knowledge-map AI is on) and its deterministic stand-in only knows five RAG questions — and the one AI that is on can't run because the model name in the config is wrong, so it too quietly falls back to the canned RAG demo. It stops when we (1) fix the model id, (2) turn on the assessment + curriculum AI, (3) make failures show an explicit "generation failed" state instead of the RAG demo, and (4) regenerate the remaining dashboard tiles from the user's own answers.*
- **Top blocking defects:** wrong model id (B1); assessment/curriculum LLM disabled (B2); RAG-only deterministic assessment bank (B3); silent cross-topic fallback (B4); six un-regenerated demo-clone artifacts (B5).

---

## B. Audit findings (most severe first)

| ID | Sev | Area | Symptom (observed) | Root cause | Evidence | Blast radius |
|----|-----|------|--------------------|-----------|----------|--------------|
| B1 | Blocker | LLM/Infra | Every live LLM call fails → deterministic fallback | Configured model id `hosted_vllm/Llama-3.1-70B-Instruct` rejected by gateway; endpoint itself is correct | Live: `POST {base}/chat/completions` → `HTTP 400 {"detail":"404: Model not found"}` in 10.6 s; guessed ids → `400 "Model not found"` <0.2 s. `.env` `UNIVERSITY_LLM_MODEL`; `live_client.py:48–57,145–149` | All LLM agents (currently only knowledge map) → deterministic RAG output |
| B2 | Blocker | Assessment/Curriculum | NLP goal still gets RAG questions & generic curriculum even if gateway healthy | Only `PATHAI_ENABLE_LLM_KNOWLEDGE_MAP_AGENT=true` in `.env`; assessment & curriculum LLM flags unset | `.env` (single flag present); `settings.py:39,47,51` aliases; `switches.py:32–42` (1 flag is allowed, others default deterministic) | Diagnostic + curriculum never AI-driven regardless of gateway |
| B3 | Blocker | Assessment | Diagnostic asks 5 RAG questions for any goal | Deterministic question bank is a fixed 5-item RAG set; `_select_question` falls through to it when goal keywords don't match | `assessment.py:309–322`; `canonical_demo.py:115–155` (Q1 = "Which component finds relevant documents in a RAG pipeline?") | Every user's diagnostic + all derived concept-evidence is RAG |
| B4 | Blocker | LLM/Data | Gateway hiccup silently yields another topic's canned content | `fallback_on_error=True` with `Mock*Agent` (canonical-RAG-seeded) fallback on every LLM agent; no fail-loud/no topic guard | `activation/factory.py:78–85,98–105,118–125,138–145` | Any LLM failure → RAG content shown as if real; violates "no fake / fail loud" |
| B5 | Blocker | Dashboard/Data | Dashboard tiles (quiz, critic, evaluation, progress, adaptation, resources) unrelated to user goal | Those 6 artifacts are demo-clones never regenerated; `generate` only rebuilds KM + curriculum | `workspace_factory.py:127–139`; `workspace_generation.py:58–68`; `dashboard.py:180–229` reads them straight from repos; RAG titles at `canonical_demo.py:395,398,654,510…` | 6 of 8 dashboard summaries are permanently RAG demo-clone |
| B6 | High | Assessment | Even the user's real typed answers become RAG concept-evidence | Deterministic scorer keys `_SCORE_BLUEPRINTS` by RAG question ids → RAG `ConceptEvidenceUpdate`s | `assessment.py:70–146,220–231`; consumed by `workspace_generation.py:51,58` | Knowledge-map & curriculum agent inputs are RAG even when their own LLM call succeeds |
| B7 | High | Curriculum | Curriculum is algorithmic, not AI, and generically topic-neutral | Curriculum LLM flag off (B2) → deterministic curriculum agent; Rebuild-29 made it topic-general but not real AI | `.env`; `switches.py`; recap `rebuild-29:141` | Curriculum screen never REAL_AI |
| B8 | Med | LLM/Infra | When it doesn't 400, gateway sometimes hangs > timeout | Gateway intermittently stalls; `/models` w/ auth hung 3×20 s; app timeout 30 s × `LLM_MAX_RETRIES=2` is synchronous in-request | Live `/models` w/ auth → 000 after 20 s ×3; `.env` `LLM_TIMEOUT_SECONDS=30`, `LLM_MAX_RETRIES=2`; `live_client.py:64` | Slow interactive requests; user waits up to ~60–90 s before fallback |
| B9 | Med | Data | `knowledge_map.assessment_session_id` dangles at seed | Clone references a re-IDed assessment id with no cloned session | `workspace_factory.py:90–94`; `dashboard.py:251–260` swallows `NotFoundError` → `assessment_summary=None` until a live session exists | Dashboard assessment tile null until live assessment; tolerated |
| B10 | Med | Frontend | 8 sidebar items are dead placeholders | No routes/pages for Goal, Progress, Resources, Quiz, Adaptation, Critic Review, Evaluation, Agents | `app-shell.tsx:38–47` (`COMING_SOON_LINKS`), `309` disabled render | Data exists (as demo-clone) but no screen to view/verify it |
| B11 | Low | Docs/Integrity | Phase reports assert "gateway timing out (external)" as root cause | Mis-diagnosis: it's a wrong model id (400), not an outage | recap `rebuild-29:103–108,148–155`; contradicted by B1 live evidence | Future work misled to "wait for gateway" instead of fixing config |

**Failure scenarios (Blockers/High):**
- **B1:** Any user completes a diagnostic → `WorkspaceGenerationService.generate` calls the LLM knowledge-map agent → `POST …/chat/completions` returns 400 "Model not found" → `LLMProviderError` → `fallback_on_error` → `MockKnowledgeMapAgent` → RAG knowledge map. Expected: NLP knowledge map. Observed: RAG.
- **B2/B3:** New user, goal "Learn NLP" → `POST /me/assessment/start` → `AssessmentAgentService._generate_question` → `self.agent` is `MockAssessorAgent` (LLM off) → `_select_question` returns `demo.ASSESSMENT_QUESTIONS[0]` → UI shows "Which component finds relevant documents in a RAG pipeline?". Expected: an NLP question.
- **B4:** Gateway flaps for one request mid-flow → that agent silently returns RAG deterministic output; UI shows it with no error banner. Expected: "generation failed, retry".
- **B5:** After a successful (hypothetical) KM+curriculum regen, user opens `/dashboard/{runId}` → quiz tile "RAG Retrieval Checkpoint", resources "FastAPI RAG endpoint example", critic/evaluation on a RAG curriculum. Expected: NLP-derived tiles.

---

## C. Interface inventory & data-provenance matrix (core artifact)

Provenance tags reflect the **current running config** (`LLM_PROVIDER=university`, only knowledge-map LLM enabled, gateway returning 400 for the configured model → all LLM calls fall back). `DEMO_CLONE` = cloned from `canonical_demo` (FAKE). `DETERMINISTIC_FALLBACK` = algorithmic, topic-general. `REAL_AI` = live LLM this session. `REAL_USER` = entered by user. `MISSING` = no route/screen.

| Screen | Route | Backend endpoint(s) | Key fields | Provenance (current) | Gap | Target end-state |
|--------|-------|---------------------|-----------|----------------------|-----|------------------|
| Login | `/login` | `POST /auth/login` | email, token | REAL_USER | — | unchanged |
| Register | `/register` | `POST /auth/register` | email, goal_text | REAL_USER | — | unchanged |
| Workspace / goal entry | `/workspace` | `POST /me/workspace`, `GET /me/workspace` | goal_text, run_id | goal_text = REAL_USER; all seeded artifacts = DEMO_CLONE | Seed injects RAG clones | Seed should create empty/placeholder-labeled artifacts, not RAG clones |
| Live diagnostic | `/assessment/live/[id]` | `POST /me/assessment/start`, `POST /me/assessment/{id}/answer`, `GET /me/assessment` | question prompt, options, concept sidebar, confidence | **question prompt = DEMO_CLONE (RAG bank)**; answer_text = REAL_USER; score/concept_evidence = DETERMINISTIC_FALLBACK (RAG-keyed); confidence/question_count = REAL_USER-derived | B2+B3+B6: questions & evidence RAG | REAL_AI NLP questions + REAL_AI scoring of real answers |
| Knowledge map | `/knowledge-map/[id]` | `GET /knowledge-map/{id}` (+ regen via `/me/workspace/generate`) | strong/weak concepts, summary, graph | Pre-generate: DEMO_CLONE. Post-generate: DETERMINISTIC_FALLBACK (LLM 400s → Mock) | B1+B4: never REAL_AI in practice | REAL_AI NLP concept map from real evidence |
| Curriculum | `/curriculum/[id]` | `GET /curriculum/{id}` (+ regen) | title, weeks, themes, topics, target_outcomes | Pre-generate: DEMO_CLONE ("Four-Week RAG Systems Build Plan"). Post-generate: DETERMINISTIC_FALLBACK (curriculum LLM off) | B2+B7 | REAL_AI NLP curriculum |
| Dashboard | `/dashboard/[runId]` | `GET /dashboard/{runId}` | run/goal/assessment/KM/curriculum/progress/quiz/resources/adaptation/critic/evaluation summaries | goal=REAL_USER; assessment=REAL_USER-derived (RAG-poisoned); KM+curriculum=DETERMINISTIC_FALLBACK; **progress, quiz, resources, adaptation, critic, evaluation = DEMO_CLONE** | B5 | every tile REAL_AI/REAL_USER, NLP |
| Static assessment view | `/assessment/[id]` | `GET /assessment/{id}` | session summary | same as live (DEMO_CLONE/DETERMINISTIC) | B3 | REAL_AI |
| Orchestration | `/orchestration/[runId]` | `GET /orchestration/{runId}` | node events, status | DEMO_CLONE (canonical completed run; `workspace_factory.py:142–177`) | run graph is fabricated "COMPLETED" | reflect real per-user run |
| Account | `/account` | `GET /auth/me` | email | REAL_USER | — | unchanged |
| Goal (sidebar) | — (no route) | — | — | MISSING | B10 | route → real goal |
| Progress | — | (`progress` API exists) | completion, weak concepts | MISSING screen; data DEMO_CLONE | B10 | route → REAL_AI progress |
| Resources | — | (`resource` API exists) | attachments | MISSING; data DEMO_CLONE (RAG) | B10 | route → REAL_AI resources |
| Quiz | — | (`quiz` API exists) | quiz, attempts | MISSING; data DEMO_CLONE (RAG) | B10 | route → REAL_AI quiz |
| Adaptation | — | (`adaptation` API) | events | MISSING; data DEMO_CLONE | B10 | route or remove |
| Critic Review | — | (`critic` API) | issues, score | MISSING; data DEMO_CLONE | B10 | route or remove |
| Evaluation | — | (`evaluation` API) | scores | MISSING; data DEMO_CLONE | B10 | route or remove |
| Agents | — | — | — | MISSING (no backend) | B10 | build or remove |

---

## D. LLM reliability & correctness audit

- **Reachability (live, key redacted):** host TCP+TLS ~140 ms; `GET {base}/models` (no auth) → **HTTP 401 in 0.4 s** → host is up. So the "external outage" narrative is refuted.
- **Endpoint correctness:** `base_url` path is `/api`; `_chat_completions_endpoint` (`live_client.py:145–149`) yields `…/api/chat/completions`. The gateway **accepts** this path (it returns structured JSON errors, not connection refusal) → **endpoint is correct**, contra hypothesis H1's "maybe needs `/v1`".
- **Model id correctness (the real bug):** `POST …/chat/completions` with the configured `hosted_vllm/Llama-3.1-70B-Instruct` → **HTTP 400 `{"detail":"404: Model not found"}`** (10.6 s). Bare `Llama-3.1-70B-Instruct`, `meta-llama/…`, lowercase → **400 `"Model not found"` in <0.2 s**. The correct id could not be enumerated because `GET /models` **with** auth hangs (0 bytes, 20 s ×3) — an operator must obtain the exact id from the gateway provider. **Action: fix `UNIVERSITY_LLM_MODEL` to the gateway's real id and confirm a 200.**
- **Auth:** `Authorization: Bearer <key>` is sent (`live_client.py:58–60`); no-auth `/models` 401 confirms the header is required and structurally correct.
- **Payload:** sends `response_format: {"type":"json_object"}` + a "Return strict JSON only" system message (`live_client.py:51–57`). Fine for an OpenAI-compatible/vLLM gateway, but confirm this gateway honors `response_format` once the model id is fixed; if not, structured parsing (`structured_output.py`) must tolerate fenced/loose JSON.
- **Timeouts/retries vs interactive budget:** effective per-call timeout = `min(request.timeout, self.timeout_seconds)` = **30 s** (`live_client.py:64`, `.env`), × `LLM_MAX_RETRIES=2`. Diagnostic runs **synchronously in-request**; a slow/hanging gateway can block a single HTTP handler ~60–90 s before falling back (B8). For a turn-by-turn diagnostic this is a poor interactive budget — consider a shorter per-call timeout for assessment + background/async generation for KM/curriculum.
- **Fallback policy (the core correctness defect):** `fallback_on_error=True` + `Mock*Agent` fallback (canonical-RAG-seeded) on **all four** LLM agents (`activation/factory.py`). Per the owner's rule this must become **fail-loud + topic-safe**: on real LLM failure, surface an explicit "generation failed / retry" state, never cross-topic canned content. If a degraded deterministic mode is kept at all, it must be topic-general (no RAG vocabulary) and **labeled** in the UI.

---

## E. Data lifecycle audit

- **Seeded at workspace creation (`workspace_factory.py:95–139`):** goal (real text/profile) + re-IDed clones of run, knowledge_map, curriculum, 7 resource_attachments, progress_state, quiz, quiz_attempt, adaptation_event, critic_review, evaluation_report — **all RAG**. No assessment session is seeded (real one created live).
- **Regenerated by `POST /me/workspace/generate` (`workspace_generation.py:49–69`):** **only** knowledge_map + curriculum, in place (reusing existing ids). Requires a COMPLETED live session or 409 (`AssessmentNotCompleteError`).
- **Never touched:** quiz, quiz_attempt, critic_review, evaluation_report, progress_state, adaptation_event, resource_attachments → remain RAG demo-clone forever (B5). `orchestration run` is a fabricated "COMPLETED" graph (`workspace_factory.py:142–177`).
- **Orphaned on reset:** `WorkspaceService.reset` re-seeds a fresh clone (new run/ids); need to confirm old artifacts are deleted vs. left dangling (repo-level; recommend an explicit cascade in P6).
- **Dangling refs:** `knowledge_map.assessment_session_id` points at a re-IDed id with no cloned session (`workspace_factory.py:90–94`); `dashboard.py:251–260` swallows the `NotFoundError` → `assessment_summary=None` until a live session exists (B9, tolerated).
- **Null/stale dashboard summaries:** `assessment_summary` null until live assessment (B9); `knowledge_map`/`curriculum` summaries reflect DETERMINISTIC_FALLBACK after generate; `progress/quiz/critic/evaluation/adaptation/resources` are always the cloned RAG values.

---

## F. Phase-by-phase remediation plan (review & approve before implementation)

> Sequencing note: the given P1 ("make the gateway work") is right as the unblocker, but P1 as-scoped is **mostly a config fix (model id) plus turning on the assessment/curriculum flags**, not app surgery — and P2 (fail-loud) must land **with** P1 so a still-flaky gateway can't keep silently serving RAG. B5 (un-regenerated artifacts) is independent and can proceed in parallel once the agents exist.

### P1 — Make the real LLM path succeed (config + activation)
- **Goal:** a live non-RAG generation actually runs through the gateway.
- **Scope (in):** correct `UNIVERSITY_LLM_MODEL` to the gateway's real id (confirm via a 200 from a minimal chat call); enable `PATHAI_ENABLE_LLM_ASSESSMENT_AGENT` + `PATHAI_ENABLE_LLM_CURRICULUM_AGENT` alongside knowledge map (the 3-way combo is already on the allowlist, `allowlist.py:27`); tune `LLM_TIMEOUT_SECONDS`/`LLM_MAX_RETRIES` to real latency. **(out):** no code redesign.
- **Files:** `.env` (operator, untracked); optionally `.env.example` docs; `docs/operations/` note on model id.
- **Tests:** opt-in live smoke (`test_live_llm_spike_optional.py`) must pass with a 200; add an opt-in live assessment-question test asserting a non-RAG prompt for an NLP goal.
- **Done when:** a live `POST /chat/completions` returns 200; opt-in live diagnostic returns an NLP question.
- **Risk/rollback:** gateway still flaps → P2 covers UX; revert = unset flags.

### P2 — Fail-loud fallback contract (no cross-topic canned content)
- **Goal:** on real LLM failure, surface explicit "generation failed / retry", never RAG.
- **Scope (in):** change the fallback policy so LLM-agent failures propagate a typed "generation unavailable" state to the service/API/UI instead of returning RAG-seeded `Mock*Agent` output; if any deterministic degraded mode is retained, make it topic-general and UI-labeled. **(out):** removing deterministic agents entirely (tests depend on them offline).
- **Files:** `activation/factory.py` (fallback wiring), agent service layer, an error DTO + API mapping, dashboard/assessment/KM/curriculum frontend states.
- **Tests:** unit — LLM failure yields the error contract, not RAG; scope-security tests stay green; default suite stays offline.
- **Done when:** with a deliberately broken model id, the UI shows an explicit failure state and **zero** RAG content.
- **Risk:** breaking the offline default suite → keep deterministic agents available for tests behind an explicit switch, not as a silent runtime fallback.

### P3 — Genuinely goal-driven diagnostic (questions + scoring)
- **Goal:** NLP goal → NLP questions and NLP-scored evidence.
- **Scope (in):** rely on the LLM assessment agent for question generation and scoring (enabled in P1); ensure the deterministic path, when used at all, does not emit RAG vocabulary (Rebuild-29 partly did this for focus, but `_select_question`/`_SCORE_BLUEPRINTS` are still RAG-bound — B3/B6). **(out):** new question UI.
- **Files:** `agents/llm/assessment.py`, `agents/deterministic/assessment.py`, `agents/services/assessment.py`.
- **Tests:** interaction test already proves handoff; add a scoring test that real answers → goal-relevant concept-evidence (fake client).
- **Done when:** live NLP diagnostic asks NLP questions and produces NLP concept-evidence.

### P4 — Regenerate ALL downstream artifacts from the assessment
- **Goal:** eliminate every DEMO_CLONE that reaches a screen (quiz, critic, evaluation, progress, adaptation, resources).
- **Scope (in):** extend `WorkspaceGenerationService.generate` (and/or the orchestration graph) to (re)build quiz, critic review, evaluation, progress, resources from the regenerated KM/curriculum + assessment, via their agents; seed-time should stop injecting RAG clones (create placeholders labeled "not yet generated"). **(out):** new agents beyond existing ones.
- **Files:** `workspace_generation.py`, `workspace_factory.py`, the quiz/critic/evaluation/progress/resource services + agents, dashboard service.
- **Tests:** per-artifact regen tests (fake client) asserting NLP-derived, non-RAG output; dashboard payload test asserting no `canonical_demo` ids/titles survive.
- **Done when:** dashboard for an NLP user has zero RAG/demo-clone tiles.

### P5 — Wire or retire the 8 "Coming soon" screens
- **Goal:** each sidebar item either routes to a real, backed screen or is removed.
- **Scope:** build `app/(name)/page.tsx` for the ones with real endpoints (Goal, Progress, Resources, Quiz, Critic, Evaluation) reading the regenerated data; remove/disable-with-honest-reason those without backing (Agents). Keep existing component scaffolding/interfaces.
- **Files:** `frontend/app/**`, `frontend/components/**`, `app-shell.tsx:38–47`.
- **Done when:** no dead placeholder shows fabricated data; every visible route renders real per-user content.

### P6 — Data-lifecycle hardening + async generation UX
- **Scope:** reset cascade (delete superseded artifacts); resolve/remove the dangling `assessment_session_id` seed ref; make dashboard summaries explicit about "pending generation" vs data; move KM/curriculum/downstream generation to a background run with a progress UI if synchronous latency (B8) is too high.
- **Done when:** reset leaves no orphans; no null summary is ambiguous; slow generation doesn't block the request thread.

### P7 — Tests & verification
- **Scope:** extend the deterministic offline suite for P2–P4 contracts; add an opt-in live end-to-end (register → NLP goal → diagnostic → generate → dashboard) asserting zero RAG. Keep default suite offline/green.
- **Done when:** `pytest` green offline; opt-in live E2E passes against a fixed gateway.

---

## G. Acceptance test (definition of done)

Not yet passable — blocked by B1–B5. To close: register a new user; goal "Learn NLP";
complete the diagnostic (**questions must be about NLP, not RAG** — currently fails at
`assessment.py:309`/`canonical_demo.py:119`); generate (**KM + curriculum must be NLP** —
currently DETERMINISTIC_FALLBACK); open the dashboard (**every tile NLP-derived** —
currently 6 tiles DEMO_CLONE). Prove with the actual `GET /me/assessment`,
`/dashboard/{runId}` JSON and that user's MongoDB documents (no `canonical_demo` ids/titles),
plus per-screen screenshots. Any surviving DEMO_CLONE/MOCK field = not closed.

---

### Live re-test log — 2026-07-13 (after LLM API key rotation)

Operator rotated the LLM API key and asked to re-verify. Result (key/host redacted):

- **Auth now passes.** With the new key, `POST {base}/api/chat/completions` returns
  `HTTP 400 {"detail":"Model not found"}` fast and consistently (~0.2 s ×6), i.e. a
  **401 is no longer produced** — the key is accepted. The earlier intermittent 70 s / 20 s
  hangs are the gateway's own flakiness (B8), not auth.
- **B1 is unchanged and remains the hard blocker.** Every model id tried is still rejected
  with `"Model not found"`: `hosted_vllm/Llama-3.1-70B-Instruct` (configured),
  `Llama-3.1-70B-Instruct`, `meta-llama/Meta-Llama-3.1-70B-Instruct`,
  `Meta-Llama-3.1-70B-Instruct`, `meta-llama/Llama-3.1-8B-Instruct`,
  `Llama-3.3-70B-Instruct`, `llama-3.1-70b`, `default`, `gpt-3.5-turbo`.
- `GET {base}/models` **with** the new key still times out (000) across 5 attempts — the
  model-list endpoint is unavailable, so the correct id cannot be self-discovered.
- **Net:** the key rotation resolves auth but does **not** unblock generation. **P1 still
  requires the gateway's exact served model id** (the `--served-model-name` the vLLM/LiteLLM
  gateway was launched with) from the provider. Until then, all LLM calls 400 → silent RAG
  fallback (B4) → the reported symptom persists.

### Resolution update — 2026-07-13 (c): switched to Groq, LLM path now works

Owner elected to use a **Groq** OpenAI-compatible gateway (`gsk_` key). Verified live and
in-code this session:

- **Gateway works (B1 → resolved).** `GET https://api.groq.com/openai/v1/models` → 200 in
  0.6 s; chat completion with `llama-3.3-70b-versatile` → 200 in ~0.25 s; the app's own
  `OpenAICompatibleLiveLLMClient` (including `response_format: json_object` + structured
  parsing) returns a valid parsed object. The endpoint path (`/openai/v1/chat/completions`)
  and `response_format` are accepted. Groq is fast and reliable, unlike the prior gateway
  (which was reachable but had no matching model and flapped — B8).
- **Config switched (B2 → resolved).** `.env` now sets `LLM_PROVIDER=groq` and the
  higher-precedence `LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY` triplet to Groq (the old
  `university` values are left inert as fallback, not destroyed), and enables the
  **assessment + knowledge_map + curriculum** LLM flags together — the allowlisted 3-way
  combo (`allowlist.py:27`). `resolve_agent_integration_switches` resolves all three to
  `llm` with no `ActivationConfigError`; `Settings.live_llm_configured` is `True`.
- **NEW finding, now fixed — structured-output prompt fragility (was masked by the dead
  gateway).** Once the gateway actually responded, all three LLM agents initially produced
  topic-correct but **schema-invalid** JSON, which (with `fallback_on_error=True`) would
  have silently fallen back to RAG anyway. Root cause: the prompts named required fields
  but not the schema's id/enum **formats**, so `llama-3.3-70b` emitted natural values the
  validator rejects:
  - assessment: `question_id="NLP_001"` (needs `question_*`), `difficulty="easy"` (needs
    `beginner|intermediate|advanced`);
  - knowledge map: `prerequisites=["Linear Algebra"]` (needs lowercase snake_case ConceptIds);
  - curriculum: omitted required `week_id` / `estimated_hours` / `learning_outcomes` /
    topic `description` / `sequence_order`.
  Fixed by hardening the three prompt builders (`app/agents/llm/assessment.py`,
  `knowledge_map.py`, `curriculum.py`) to state the exact id prefixes, enum values, numeric
  ranges, and full required-field lists. **After the fix**, driven live through Groq with
  fallback disabled, for goal "Learn NLP": assessment → *"What does NLP stand for?"*;
  knowledge map → *NLP Fundamentals / Tokenization / Retrieval*; curriculum → *"NLP
  Fundamentals"* with weeks *Introduction to NLP → Tokenization & Text Preprocessing → NLP
  Applications → Advanced NLP Topics*. Zero RAG. Offline suite **422 passed**, ruff + mypy
  clean.

**Findings now resolved:** B1 (gateway/model), B2 (flags), B7 (curriculum LLM off), B8
(flaky gateway — Groq is stable), B11 (mis-diagnosis, corrected here), plus the newly
surfaced prompt-robustness defect (the live blocker once B1 was gone).

**Findings STILL OPEN (next priorities):**
- **B4 — silent fallback still exists.** `fallback_on_error=True` remains on all agents. If
  a Groq call ever fails/invalidates, the user still silently gets RAG deterministic output
  with no error. Fail-loud (P2) is not yet done; it is now the top remaining correctness gap.
- **B5 — six dashboard artifacts still demo-clone.** Quiz, critic, evaluation, progress,
  adaptation, resources are still cloned RAG and never regenerated (P4). The assessment,
  knowledge map, and curriculum are now REAL_AI; the rest of the dashboard is still FAKE.
- **B6** is largely addressed for the LLM path (real scoring), but the deterministic
  fallback scorer is still RAG-keyed (only matters if B4 fallback triggers).
- **B3** deterministic assessment bank is still RAG-only; acceptable *only* as long as it's
  never reached (depends on B4 being fixed to fail loud rather than fall back).
- **B9 / B10** unchanged (dangling seed ref; 8 unrouted sidebar screens).

**Net for the owner:** the NLP diagnostic, knowledge map, and curriculum are now genuinely
AI-generated for the user's goal. Two things still lie on the dashboard until P4: the quiz,
critic, evaluation, progress, resources, and adaptation tiles. And until P2, a transient LLM
error would still quietly show RAG instead of an honest "generation failed" — so P2 + P4 are
the next phases.

### Verification performed this session
- Static trace of the full path (frontend → routes → services → agent switch → live client → deterministic agents → `canonical_demo`), all cited above.
- Live gateway isolation (curl, key/host redacted): reachability, endpoint, model-id, `/models`, timing — refuting the "outage" diagnosis and pinpointing the model-id 400.
- Config read from untracked `.env` (key **names** and **non-secret** values only; secrets never printed).
- Not run this session: full stack + MongoDB E2E for a live NLP user (blocked by B1 model id; requires the correct model id from the gateway operator). Recommended as the first step of P1 verification.
