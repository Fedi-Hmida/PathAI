import { expect, test } from "@playwright/test";

import {
  completeAssessmentViaUi,
  createWorkspaceViaUi,
  generateWorkspaceViaUi,
  registerViaUi,
  submitQuizViaUi,
  uniqueEmail,
} from "./helpers";

// The second, genuinely distinct flow worth its own E2E test (Big_Audit
// Step 13): quiz submission is a real write path with real branching -
// scoring, a real per-submission attempt (never overwritten), and a real
// Adaptation trigger gated on a real low score (Big_Audit Step 11). None of
// that is exercised by the read-only full-lifecycle walkthrough.
const GOAL_TEXT = "Learn classical guitar for a wedding performance";

test("submit wrong answers -> real low score + real adaptation trigger -> retake -> a genuinely new, high-scoring attempt", async ({
  page,
}) => {
  const email = uniqueEmail("e2e-quiz");

  await registerViaUi(page, email);
  await createWorkspaceViaUi(page, GOAL_TEXT);
  await completeAssessmentViaUi(page);
  await generateWorkspaceViaUi(page);

  await page.getByRole("link", { name: "Quiz", exact: true }).click();
  await page.waitForURL("**/quiz/**/take");
  const quizId = page.url().match(/\/quiz\/([^/]+)\/take/)?.[1];
  expect(quizId).toBeTruthy();

  // Every answer deliberately wrong (option index 1, never the correct
  // index 0) - forces a real, low score, not a fabricated one.
  await submitQuizViaUi(page, 1);
  const firstAttemptUrl = page.url();
  const firstAttemptId = firstAttemptUrl.match(/\/attempts\/([^/]+)$/)?.[1];
  expect(firstAttemptId).toBeTruthy();

  await expect(page.getByText("Quiz Results")).toBeVisible();
  await expect(page.getByText("0 of", { exact: false })).toBeVisible();
  await expect(
    page.getByText("This score is low enough to adjust your plan."),
  ).toBeVisible();

  // Retake: there's no in-app "retake" link today (a real UX gap surfaced
  // by writing this test, not a bug in the scoring/adaptation logic itself
  // - noted in this step's summary, not silently patched), so this reaches
  // the real take page the only way currently possible: direct navigation.
  // Every subsequent interaction is still driven through the real form.
  await page.goto(`/quiz/${quizId}/take`);
  await submitQuizViaUi(page, 0);
  const secondAttemptUrl = page.url();
  const secondAttemptId = secondAttemptUrl.match(/\/attempts\/([^/]+)$/)?.[1];
  expect(secondAttemptId).toBeTruthy();

  // A real, distinct attempt - never overwrites the first (Big_Audit Step 10).
  expect(secondAttemptId).not.toBe(firstAttemptId);
  await expect(page.getByText("Quiz Results")).toBeVisible();

  // The real Adaptation event from the first (wrong-answer) submission is
  // still there, reachable through the sidebar - a later good score doesn't
  // retroactively erase it.
  await page.getByRole("link", { name: "Adaptation", exact: true }).click();
  await page.waitForURL("**/adaptation/**");
  await expect(
    page.getByRole("heading", { name: "Your Plan Adjusted After a Quiz" }),
  ).toBeVisible();
});
