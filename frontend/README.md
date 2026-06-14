# PathAI Frontend

Next.js frontend for PathAI.

## Local Setup

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

If PowerShell blocks `npm.ps1`, use the Windows command shim instead:

```powershell
npm.cmd install
npm.cmd run dev
```

Phase 0 only provides the frontend shell. Onboarding, dashboard, week view, quiz, and settings screens are implemented in later phases.

## Phase 5 Curriculum Mini-Scope

The curriculum dashboard mini-scope is available at:

```text
/dashboard/demo
/dashboard/{curriculum_id}
```

`/dashboard/demo` reads the backend development example endpoint. `/dashboard/{curriculum_id}` reads a generated curriculum from the backend Phase 5 in-memory store.

The Phase 5 backend does not persist curricula to MongoDB yet. Restarting the backend clears generated curricula until persistence is implemented in a later phase.

## P1 No-Auth Demo Flow

The local no-auth guided demo is available at:

```text
/demo
```

It calls the current backend demo endpoints for:

- assessment,
- knowledge map finalization,
- curriculum generation,
- resource attachment,
- critic review,
- progress update,
- quiz generation and scoring,
- adapter/replanning,
- synthetic evaluation,
- service-backed backend orchestration verification.

Run it locally with:

```powershell
cd frontend
npm.cmd run dev
```

Then open:

```text
http://localhost:3000/demo
```

This page is intentionally local/demo scoped. It does not implement login,
sessions, protected routes, production persistence, Docker, or deployment.

## UI-0 Foundation

The UI-0 pass adds frontend architecture foundations for the next production UI
phases while preserving the existing `/demo` behavior.

Design system foundation:

```text
styles/tokens.css
components/ui/
components/layout/
```

Shared API foundation:

```text
lib/api/client.ts
lib/api/types.ts
lib/api/runtime.ts
```

`lib/api/client.ts` centralizes the API base URL, JSON request handling,
`no-store` behavior, and backend error-envelope parsing. Existing demo and
curriculum helpers remain working; later UI phases should migrate feature API
helpers to the shared client as screens are rebuilt.

Validation commands:

```powershell
cd frontend
npm.cmd run lint
npm.cmd exec tsc -- --noEmit
npm.cmd run build
```

This frontend remains local no-auth demo scope. UI-0 does not add
authentication, Docker, deployment, production persistence, or protected routes.

## UI-1 App Shell And Navigation

UI-1 adds the reusable product shell used by `/` and `/demo`:

```text
components/layout/AppShell.tsx
components/layout/NavigationRail.tsx
components/layout/TopStatusBar.tsx
components/workflow/WorkflowStepper.tsx
```

The shell provides:

- PathAI command-center framing,
- local no-auth mode visibility,
- workflow navigation with coming-soon states,
- backend health/readiness/LLM mode status,
- a reusable workflow stepper for the PathAI pipeline.

Runtime status uses:

```text
lib/api/runtime.ts
```

The LLM status calls the safe development config endpoint and never exposes API
keys. If dev endpoints are disabled, the UI shows the LLM config as unavailable.

Run the current local UI with:

```powershell
cd frontend
npm.cmd run dev
```

Then open:

```text
http://localhost:3000
http://localhost:3000/demo
```

Validation commands:

```powershell
npm.cmd run lint
npm.cmd exec tsc -- --noEmit
npm.cmd run build
```

UI-1 does not implement the later product screens. Assessment rebuild,
interactive quiz, deep resources/critic/adaptation screens, authentication,
Docker, and deployment remain outside this phase.

## UI-2 Goal Intake And Assessment

UI-2 adds the first product workflow route:

```text
/learn/new
```

This route lets a local no-auth learner:

- enter a learning goal,
- choose timeline, hours/week, target level, and question limit,
- start an assessment session,
- answer backend-generated diagnostic questions manually,
- see answer feedback and concept matches,
- track assessment progress and confidence,
- manually finalize the knowledge map.

Assessment UI files:

```text
components/assessment/
lib/api/assessment.ts
app/learn/new/page.tsx
```

The route stops at the knowledge map. It does not generate curriculum, attach
resources, run the critic, or launch quiz/adaptation screens yet. Those remain
future UI phases.

Run locally:

```powershell
cd frontend
npm.cmd run dev
```

Then open:

```text
http://localhost:3000/learn/new
```

Validation commands:

```powershell
npm.cmd run lint
npm.cmd exec tsc -- --noEmit
npm.cmd run build
```

## Stitch Command Center Dashboard

The Stitch command-center implementation is available at:

```text
/command-center
```

This route converts the exported Stitch web layout into maintainable Next.js
components and CSS modules. It uses deterministic visual mock data so the
dashboard can be inspected without authentication, MongoDB persistence, a real
LLM call, or backend orchestration state.

Dashboard implementation files:

```text
app/command-center/page.tsx
components/dashboard/
lib/demo/commandCenterMock.ts
```

The command center includes:

- dark navy navigation rail,
- top command/status bar,
- premium current learning path card,
- mastery progress ring,
- agent orchestration pipeline,
- curriculum path timeline,
- knowledge map,
- interactive-looking quiz module,
- recommended resources,
- critic analysis inspector,
- adaptation protocol inspector,
- architecture health metrics.

The existing backend-connected smoke path remains:

```text
/demo
```

Use `/demo` when you want to verify live local backend connectivity. Use
`/command-center` when you want to review the polished dashboard direction from
the Stitch export.
