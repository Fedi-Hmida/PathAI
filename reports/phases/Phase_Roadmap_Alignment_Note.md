# PathAI Phase Roadmap Alignment Note

Status: Roadmap alignment note  
Project: PathAI  
Created: 2026-07-05  

## Purpose

This note clarifies phase naming after the completed Rebuild-2 work introduced a numbering drift relative to the canonical roadmap in `docs\architecture\MAIN.md`.

`docs\architecture\MAIN.md` remains the canonical source of truth for roadmap numbering and phase names.

## Alignment Decision

The completed work documented as:

```text
Rebuild-2: Core Schemas, Contracts, And Mock LLM Fixtures
```

included both of the following roadmap concepts from `MAIN.md`:

- `Rebuild-2: Core Schemas And Contracts`
- `Rebuild-3: Mock LLM And Deterministic Agent Fixtures`

Because the Rebuild-2 implementation already completed the mock fixture scope, the canonical `Rebuild-3: Mock LLM And Deterministic Agent Fixtures` is considered functionally completed as part of the Rebuild-2 result.

## Next Canonical Phase

Future phase naming should continue from the canonical roadmap in `MAIN.md`.

The next canonical phase should therefore be:

```text
Rebuild-4: Fake Repositories And Service Skeleton
```

Future reports and implementation prompts should use `Rebuild-4` for the fake repository and service skeleton phase.

## Historical Note

Existing Rebuild-2 file names are preserved to avoid breaking phase history. The alignment notes in the Rebuild-2 action plan and result recap explain that the completed scope included both Rebuild-2 and canonical Rebuild-3 work.

