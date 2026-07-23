import type { Page } from "@playwright/test";

// Real, unique-per-run credentials against a real (fake-repository,
// deterministic-agent) backend - see playwright.config.ts for how to start
// it. Never anything from the real .env.
export function uniqueEmail(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
}

export const PASSWORD = "correcthorsebattery";

export async function registerViaUi(page: Page, email: string): Promise<void> {
  await page.goto("/register");
  await page.locator("#email").fill(email);
  await page.locator("#password").fill(PASSWORD);
  await page.locator("#confirm-password").fill(PASSWORD);
  await page.getByRole("button", { name: "Create account" }).click();
  await page.waitForURL("**/workspace");
}

export async function createWorkspaceViaUi(page: Page, goalText: string): Promise<void> {
  await page.locator("#goal-text").fill(goalText);
  await page.getByRole("button", { name: "Create my workspace" }).click();
  await page.waitForURL("**/assessment/live/**");
}

// The deterministic assessment agent asks a fixed number of questions of
// varying type (multiple_choice / self_rating / short_answer) - this
// answers whichever real question is currently on screen, then submits and
// lets the caller wait for whatever comes next (another question or the
// "Diagnostic complete" screen).
export async function answerCurrentQuestion(page: Page): Promise<void> {
  const mcOption = page.getByTestId("assessment-option").first();
  const textAnswer = page.getByPlaceholder("Type your answer...");
  const ratingButton = page.getByTestId("self-rating-3");

  // Wait for whichever input this question actually renders - by the time
  // one of these resolves, React has already torn down the previous
  // question's DOM, so there's no risk of acting on stale content.
  await Promise.race([
    mcOption.waitFor({ state: "visible" }),
    textAnswer.waitFor({ state: "visible" }),
    ratingButton.waitFor({ state: "visible" }),
  ]);

  if (await mcOption.isVisible().catch(() => false)) {
    await mcOption.click();
  } else if (await textAnswer.isVisible().catch(() => false)) {
    await textAnswer.fill("A real free-text diagnostic answer for this question.");
  }

  // Present either as the primary answer (self_rating questions) or as the
  // secondary confidence widget (every other question type) - clicking it
  // whenever it's on screen exercises the real control either way.
  if (await ratingButton.isVisible().catch(() => false)) {
    await ratingButton.click();
  }

  await page.getByRole("button", { name: "Submit", exact: true }).click();
}

export async function completeAssessmentViaUi(page: Page, totalQuestions = 5): Promise<void> {
  for (let i = 0; i < totalQuestions; i += 1) {
    await answerCurrentQuestion(page);
  }
  // CardTitle renders a <div>, not a semantic heading - match on its text.
  await page.getByText("Diagnostic complete").waitFor();
}

export async function generateWorkspaceViaUi(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Generate my learning path" }).click();
  await page.waitForURL("**/dashboard/**", { timeout: 30_000 });
  // Real bug surfaced by writing this test (reported in the Step 13 summary,
  // not silently fixed - out of this step's scope): AppShell resolves the
  // caller's own workspace/run via `getMyWorkspace()` exactly once, in an
  // effect gated on `[needsOwnWorkspace]` - which flips true immediately at
  // registration, before a workspace exists yet. A user who creates their
  // workspace afterward in the SAME session (the normal register -> create
  // -> assess -> generate flow, exercised end-to-end here for the first
  // time) never sees the sidebar's Goal/Knowledge Map/Curriculum/etc links
  // activate, because that effect never re-fires. A full reload forces a
  // fresh mount, which re-resolves it correctly - the same workaround a real
  // user hitting this would need today.
  await page.reload();
}

// Drives the real quiz-taking UI (radio select -> Next Question -> ... ->
// Submit Quiz), always picking the option at `optionIndex` for every
// question. The deterministic quiz agent always puts the correct answer at
// index 0 (confirmed by the backend's own
// `_submit_real_attempt_with_wrong_answers` test helper), so index 0 forces
// a perfect score and any other index forces every answer wrong - a real,
// deterministic way to drive either branch of the real scoring/adaptation
// logic through the actual UI, not a shortcut around it.
export async function submitQuizViaUi(page: Page, optionIndex: number): Promise<void> {
  for (;;) {
    const options = page.getByRole("radiogroup").getByRole("radio");
    await options.first().waitFor({ state: "visible" });
    await options.nth(optionIndex).click();

    const submitButton = page.getByRole("button", { name: "Submit Quiz" });
    if (await submitButton.isVisible()) {
      await submitButton.click();
      break;
    }
    await page.getByRole("button", { name: "Next Question" }).click();
  }
  await page.waitForURL("**/quiz/**/attempts/**", { timeout: 30_000 });
}
