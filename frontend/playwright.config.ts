import { defineConfig, devices } from "@playwright/test";

// Opt-in only (Big_Audit Step 13) - mirrors the backend's
// ENABLE_LIVE_MONGO_TESTS/ENABLE_LIVE_LLM_TESTS discipline: this suite needs
// a REAL backend reachable at http://localhost:8000/api/v1 (the frontend's
// default API_BASE_URL) and is never part of `npm test`, `npm run lint`, or
// any default/CI-less path. Run it with `npm run test:e2e`.
//
// The backend must be started separately, deliberately, in the repo-default
// FAKE-repository / deterministic-agent mode (no `.env`, no
// REPOSITORY_BACKEND/LLM_* overrides) - fast and fully offline/deterministic
// itself, which is exactly what this suite needs to prove: that the real
// FRONTEND flow works against the real API contract, not that Mongo
// persistence works (Step 3 already proves that separately, with its own
// opt-in live-mongo tests). From `backend/`, with the project venv:
//
//   PATHAI_ENABLE_AUTH=true JWT_SECRET_KEY=<any-local-test-string> \
//     REFRESH_COOKIE_SECURE=false \
//     .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
//
// (JWT_SECRET_KEY is required whenever auth is enabled; REFRESH_COOKIE_SECURE
// must be false for a plain-http local run - both local-only test values,
// never anything from the real .env.)
//
// This config starts the Next.js frontend itself (fast, local, the thing
// actually under test) but never the backend.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  // Both specs drive a real, multi-step session (register -> ... ->
  // generate -> several detail screens) against one shared `next dev`
  // server and one shared backend process - real resource contention, not
  // just test-isolation risk, so force serial execution rather than race
  // two full sessions through a single dev-mode server at once.
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
