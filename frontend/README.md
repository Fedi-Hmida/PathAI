# PathAI Frontend

Next.js (App Router, TypeScript) foundation for the PathAI learner UI. Rebuild-19
shipped the plumbing + design-system layer: app shell, base components, and a
typed API client. Rebuild-24 added the first feature screen, the Learner
Dashboard (`app/dashboard/[runId]/`). Remaining feature/product screens (goal,
assessment, knowledge map, curriculum, resources, quiz, adaptation) are still a
later phase.

The visual design (colors, typography) in `styles/globals.css` is sourced from
the approved Claude Design "Learner dashboard" mockup's design system (IBM Plex
Serif/Sans/Mono, indigo accent, cool blue-gray neutrals) — no longer shadcn/ui's
placeholder theme. It remains scoped to `styles/globals.css`'s CSS variables so
it can be revised without touching component code.

## Setup

```cmd
npm install
copy .env.example .env.local
```

Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local` if the backend isn't running on
the default `http://localhost:8000/api/v1`.

## Commands

```cmd
npm run dev         :: start the dev server (http://localhost:3000)
npm run build        :: production build
npm run start        :: run the production build
npm run lint          :: eslint
npm run typecheck    :: tsc --noEmit
```

## Backend dependency

The frontend expects the PathAI backend running locally (see `backend/README.md`),
by default at `http://localhost:8000`. The backend's CORS policy
(`BACKEND_CORS_ORIGINS` in `app/core/settings.py`) already allows
`http://localhost:3000` by default, so no backend changes are required to run
this frontend against a local backend.

## Structure

- `app/` — Next.js routes, layouts, page entry points, including
  `app/dashboard/[runId]/page.tsx` (Learner Dashboard).
- `components/ui/` — generic base components (button, card, input, badge,
  skeleton, alert), managed via shadcn/ui (`components.json`).
- `components/layout/` — app shell, theme provider/toggle.
- `components/dashboard/` — Dashboard-screen presentational components
  (progress ring, KPI tile, knowledge-map card, next-action card,
  curriculum week list, adaptation banner).
- `lib/api/` — typed API client (`client.ts` fetch wrapper + `ApiError`, one
  file per resource, e.g. `health.ts`, `dashboard.ts`).
- `lib/types/` — TypeScript types mirroring backend API DTOs.
- `styles/globals.css` — Tailwind v4 entrypoint and design tokens (CSS variables).
