# PathAI — Multi-Agent AI Platform Upgrade: Execution Prompt for Claude Code CLI

**Status:** Proposed — approved by project owner for planning-doc execution (see §0). Not yet implemented in code.
**Author role:** Senior AI/platform engineering brief, written for direct execution by Claude Code CLI.
**Scope:** `docs/architecture/MAIN.md`, `docs/architecture/RULES.md`, `reports/phases/Plan.md`. **Docs only — no application code changes in this pass.**

---

## 0. How to use this document (read first, this is the actual prompt)

You are Claude Code, acting as senior AI/platform engineer on PathAI. The project owner has decided PathAI should evolve from its current state — a deterministic orchestration backend with individually-gated, one-at-a-time LLM agent options — into a genuine multi-agent AI platform: multiple agents reasoning with real LLMs *within the same run*, with real data dependency between them, reachable by a real caller, and automated end-to-end.

Before writing anything:

1. **Re-verify every factual claim in §1 against the current repository state.** This brief was written from a point-in-time analysis (2026-07-09, repo at commit `e9d1353` plus an uncommitted diff completing Rebuild-14F/14G). Code moves faster than briefs. If `resolve_agent_integration_switches`, the agent inventory, or the phase list has changed, trust the code and update your understanding — don't propagate a stale claim into MAIN.md/RULES.md/Plan.md.
2. **Do not implement anything in this pass.** Your deliverable is updated planning documents plus one new phase Action Plan (per the existing convention in `reports/phases/rebuild-14/Rebuild_14_Activation_Wiring_And_Controlled_Enablement_Action_Plan.md`) that scopes the *first* implementation phase. Writing the multi-agent code itself is a separate, future, explicitly-approved phase.
3. **Everything below §1 is my (the senior engineer's) recommendation, not a spec to copy verbatim.** Where you disagree with a recommendation because the current code contradicts it, say so in your output and adjust — don't silently implement something that doesn't fit what you actually find.
4. **Follow `RULES.md` §-for-§ while editing `RULES.md` itself.** This is reflexive: the phase-discipline, layering, and secret-handling rules apply to this task too. Produce a phase recap under `reports/phases/rebuild-16/` (or whatever the correct next number is per `Plan.md`) documenting this planning update, using the mandatory recap structure (Scope, MAIN.md/RULES.md Compliance, Files Created/Updated, Work Completed, Validation, Security/Secret Handling, Not Done, Remaining Risks, Next Recommended Phase).

---

## 1. Grounded current-state summary (verify, don't trust)

- 9 agent roles exist as separate LangGraph-orchestrated steps: Assessment, Knowledge Map, Curriculum, Resource, Critic, Progress, Quiz, Adaptation, Evaluation.
- Only 4 of 9 have any LLM-backed implementation (`app/agents/llm/`): Assessment, Knowledge Map, Critic, Curriculum. The other 5 are deterministic/mock only, with no LLM path even scaffolded.
- `resolve_agent_integration_switches` (`app/agents/services/activation/switches.py`) hard-enforces **at most one** LLM agent active at a time, raising `ActivationConfigError` on 2+. This is a deliberate rollout-safety gate, not an architectural ceiling — nothing in the agent classes themselves prevents concurrent use.
- As of the latest working-tree state, all four LLM agents are independently wired and reachable via `OrchestrationContext.from_container` (Rebuild-14D/14F/14G), deterministic-by-default, with retry/fallback/observability (Rebuild-15A–D: structured retry, bounded backoff, sanitized `LoggingObserver` events on fallback).
- `app/orchestration/graph.py` is a **straight-line loader** — it assembles already-persisted artifacts (`load_goal`, `load_assessment`, …) rather than running a real generation pipeline. `MAIN.md` already aspirationally describes a true generation-pipeline graph; the code has not caught up to that description.
- `app/rag/` and `app/evaluation/` are empty packages — no retrieval exists behind Resource curation.
- Repositories are 100% in-memory fakes — no state survives a process restart.
- No HTTP route triggers orchestration end-to-end — `app/api/v1/demo.py` loads static fixtures directly, bypassing the graph entirely. This is the single biggest reachability gap: today, nothing an LLM agent produces can be seen by a real caller.
- No agent has ever been exercised against a real LLM provider in this project's history — every test and every validation run has used `FakeLLMClient`. `live_llm`-marked tests exist but are skipped by default and, per the project record, have never been run with real credentials.
- `frontend/` is empty scaffolding.

None of this is a criticism of the work done — Rebuild-12 through 15 built the boundary correctly (provider-agnostic client, retry/fallback/observability, per-agent activation gates) specifically *so that* a multi-agent upgrade could be layered on safely later. This brief is that later step.

---

## 2. What "multi-agent AI platform" must mean here (precise, testable definition)

Reject the vague version ("several agents that use AI"). Adopt this bar instead — a run only counts as genuinely multi-agent if **all** of the following hold:

1. **≥2 agents in the same orchestration run** are LLM-backed simultaneously, not deterministic stand-ins.
2. **At least one real data dependency** exists between them — e.g., the Critic agent's real LLM call consumes the Curriculum agent's real LLM output (not the deterministic curriculum, which is what happens today even when Critic is "on," because Critic can never be on at the same time as Curriculum). Parallel-but-independent LLM calls don't meet the bar; the interesting risk and the interesting product value are both in the handoff.
3. **Reachable by a real caller** — an HTTP request, not just a direct Python construction in a test. (Depends on Rebuild-18.)
4. **Observable and bounded** — an operator can see, per run, which agents actually ran in LLM mode, how many calls were made, and what it's costing/how long it took, with a hard ceiling that prevents runaway cost/latency when several agents are chained. (Extends Rebuild-15's observability work from per-agent to per-run.)
5. **Explicitly validated as a combination**, not just validated individually — the interaction between two real-AI outputs has never been tested in this project (this is a documented, open gap from the Rebuild-15D recap). "Assessment alone works" and "Critic alone works" do not imply "Assessment feeding Critic works."

If a future run has 2+ agents active but fails any of #2–#5, don't call it a multi-agent platform in any doc you write — call it what it is (parallel single-agent activation) and say so plainly.

---

## 3. The core policy pivot: from a binary gate to a graduated allowlist

**Recommendation:** Do not simply delete `ActivationConfigError`'s 2+-flags check and let any combination run. That trades a safe-but-limited system for an unvalidated one, and repeats the exact mistake Rebuild-14D's own history already corrected once (the "CORRECTED" note in `Plan.md` describes a case where flags silently activated an untested LLM agent — don't reintroduce that shape of bug at the combination level).

Instead, replace the binary gate with a **validated-combination allowlist**:

- `AgentIntegrationSwitches` resolution should check the *set* of requested LLM agents against an explicit, code-defined allowlist of combinations that have their own interaction-tested phase behind them (e.g. `frozenset({"critic", "curriculum"})`). Empty set and any single agent remain allowed by default (today's behavior, unchanged). Unlisted combinations of 2+ still raise `ActivationConfigError`, with a message naming which combination was rejected and pointing at the phase that would need to land first.
- Each new allowlisted combination is its own phase, following the exact discipline already used for single-agent rollout (14D → 14F → 14G pattern): a real interaction test asserting the second agent's behavior given the first agent's *real* LLM output (via `FakeLLMClient` with a scenario, not the deterministic fixture), a manual dry-run recap, pass-count deltas, before being added to the allowlist.
- This gives you a real multi-agent platform incrementally and provably, the same way the single-agent rollout did — rather than a flag flip that outruns what's actually been tested.

Document this as the replacement for Plan.md's currently-open decision #2 ("one-agent-at-a-time policy … closed unless the project owner wants multi-agent activation allowed instead") — it *is* that decision, made concretely rather than left open.

---

## 4. Architectural changes this implies (for MAIN.md, to sequence into future phases — not to build now)

Record these as forward-looking MAIN.md/Plan.md content, each as its own future phase, not as work to start immediately:

1. **Run-level budget/circuit-breaker**, above the existing per-agent retry/fallback. Once 2+ agents can chain real LLM calls in one run, an operator needs a hard ceiling (max total LLM calls per run, max wall-clock per run) independent of any single agent's own retry policy — extends Rebuild-15's `LLMReliabilityObserver` from per-agent to a per-run aggregate.
2. **Graph evolution from straight-line loader toward the generation pipeline MAIN.md already describes.** A meaningful Critic→Curriculum feedback loop is a graph-shape change (conditional edges / re-entry), not just an agent-wiring change. Flag explicitly in MAIN.md that this is the point where the "aspirational" generation-pipeline graph and the actual `graph.py` are meant to converge — and that convergence is itself a scoped phase, not a side effect of enabling more flags.
3. **RAG (Rebuild-16) and persistence (Rebuild-17) are prerequisites for a *demonstrable* multi-agent run**, not just nice-to-haves alongside it — without them, a Resource agent has nothing grounded to hand a Critic agent, and nothing about a multi-agent run survives to be inspected afterward. Sequence the combination-allowlist phases *after* 16–18 land, or explicitly justify running them in test-only mode first if the owner wants validation before investing in RAG/persistence.
4. **Interaction test suite as a first-class category**, alongside the existing `*_behavior.py` / `*_events.py` / `*_orchestration.py` / `*_scope_security.py` split — e.g. `*_agent_interaction.py` — specifically for "agent A's real output feeds agent B's real input" cases. Name this convention explicitly in the Testing Conventions section of the relevant docs so future phases follow it without re-deriving it.

---

## 5. Concrete deliverables for this execution pass

When you (Claude Code) execute this brief, produce:

1. **`docs/architecture/MAIN.md`** — update to state plainly, near wherever it currently describes the aspirational generation-pipeline graph, that (a) this is now an approved direction, (b) it is not yet implemented, (c) it converges with `graph.py` in a specific future phase (name the phase number you land on in Plan.md). Do not rewrite MAIN.md's existing contracts/schemas — only the sections describing orchestration shape and multi-agent policy.
2. **`docs/architecture/RULES.md`** — add an explicit rule set for multi-agent operation: the validated-combination-allowlist requirement (§3), the run-level budget requirement (§4.1), the interaction-test-category requirement (§4.4), and a restatement that all existing layering/security/secret rules apply unchanged at multi-agent scale (agents still don't touch persistence, redaction still applies, deterministic default suite still can't require a real LLM). Add this as a new numbered section rather than editing existing numbered rules, to avoid renumbering references elsewhere in the repo.
3. **`reports/phases/Plan.md`** — insert the new phase(s) this implies, correctly numbered relative to existing 16/17/18/19/20/21, status `NOT STARTED`, with a one-line description each. Close open decision #2 by replacing it with a reference to §3 of this brief. Do not mark anything `DONE` — this pass only plans.
4. **A new phase Action Plan** for the *first* concrete implementation phase (likely: "define the run-level budget/observer aggregate" or "land the first validated 2-agent combination, e.g. Curriculum→Critic" — pick whichever has the smallest safe blast radius, matching this project's established safest-first pattern from Rebuild-15's own A/B/C/D split), following the structure of `Rebuild_14_Activation_Wiring_And_Controlled_Enablement_Action_Plan.md` or `Rebuild_15_Prompt_Quality_And_Reliability_Hardening_Action_Plan.md`. This is a plan, not code.
5. **A phase recap** for this planning-update pass itself, filed under the correct `reports/phases/rebuild-N/` directory, per the mandatory structure in `CLAUDE.md`.

---

## 6. Guardrails that do not change

- Layering (`Frontend -> API routes -> Services -> Repositories -> DB`, `Services -> LangGraph orchestration -> Agents -> LLM/RAG/Evaluation`) is unaffected by this upgrade and must not be loosened to make multi-agent wiring easier.
- `.env` is never read, printed, copied, modified, or exposed. No secret-like value appears in any doc this pass touches.
- The default test suite still requires no real LLM, network, or MongoDB. Multi-agent interaction tests are deterministic (`FakeLLMClient` scenarios), exactly like every existing LLM-agent test.
- Phase discipline holds: this pass scopes planning docs and one action plan only. It does not implement the allowlist, the budget aggregate, or any new agent.

---

## 7. What "done" looks like for this specific execution pass

- `MAIN.md`, `RULES.md`, `Plan.md` diffs exist and are internally consistent with each other (no doc contradicts another on phase numbering or policy).
- A new Action Plan doc exists for the first real implementation phase, small enough to execute in one sitting, matching this repo's existing safest-first phase-splitting style.
- A phase recap exists for this pass itself.
- Nothing in `app/` changed.
- You (Claude Code) end your turn by stating, in your own words, what you'd recommend as the very next command to run — not by silently starting implementation.
