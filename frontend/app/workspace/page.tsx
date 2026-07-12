"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { RequireAuth } from "@/components/auth/require-auth";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { getMyAssessment, startAssessment } from "@/lib/api/assessment";
import { ApiError } from "@/lib/api/client";
import { createMyWorkspace, getMyWorkspace, resetMyWorkspace } from "@/lib/api/workspace";

const MIN_GOAL_LENGTH = 5;
const MAX_GOAL_LENGTH = 500;

export default function WorkspacePage() {
  return (
    <RequireAuth>
      <WorkspaceView />
    </RequireAuth>
  );
}

type ViewState =
  | { kind: "loading" }
  | { kind: "empty" }
  | { kind: "has_workspace"; runId: string; assessmentInProgressId: string | null }
  | { kind: "error"; message: string };

function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : "Unable to reach the PathAI backend.";
}

function WorkspaceView() {
  const router = useRouter();
  const [state, setState] = React.useState<ViewState>({ kind: "loading" });
  const [busy, setBusy] = React.useState(false);
  const [goalText, setGoalText] = React.useState("");
  const [resetGoalText, setResetGoalText] = React.useState("");
  const goalTextValid = goalText.trim().length >= MIN_GOAL_LENGTH;
  const resetGoalTextValid = resetGoalText.trim().length >= MIN_GOAL_LENGTH;

  React.useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const workspace = await getMyWorkspace();
        if (cancelled) {
          return;
        }
        if (!workspace) {
          setState({ kind: "empty" });
          return;
        }
        // A page reload/return visit mid-diagnostic should offer to resume it
        // rather than send the learner straight to a dashboard whose
        // assessment summary is still empty.
        const assessment = await getMyAssessment();
        if (cancelled) {
          return;
        }
        setState({
          kind: "has_workspace",
          runId: workspace.run_id,
          assessmentInProgressId:
            assessment?.status === "in_progress" ? assessment.assessment_session_id : null,
        });
      } catch (error) {
        if (!cancelled) {
          setState({ kind: "error", message: errorMessage(error) });
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  async function goToLiveAssessment() {
    const session = await startAssessment();
    router.replace(`/assessment/live/${session.assessment_session_id}`);
  }

  async function handleCreate() {
    if (!goalTextValid) {
      return;
    }
    setBusy(true);
    try {
      await createMyWorkspace(goalText.trim());
      await goToLiveAssessment();
    } catch (error) {
      setState({ kind: "error", message: errorMessage(error) });
    } finally {
      setBusy(false);
    }
  }

  async function handleReset() {
    if (!resetGoalTextValid) {
      return;
    }
    setBusy(true);
    try {
      await resetMyWorkspace(resetGoalText.trim());
      await goToLiveAssessment();
    } catch (error) {
      setState({ kind: "error", message: errorMessage(error) });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Workspace
        </span>
        <h1 className="font-goal text-foreground mt-1 text-lg font-medium">Your learning workspace</h1>
      </div>

      {state.kind === "error" ? (
        <Alert variant="destructive">
          <AlertTitle>Something went wrong</AlertTitle>
          <AlertDescription>{state.message}</AlertDescription>
        </Alert>
      ) : null}

      {state.kind === "empty" || state.kind === "error" ? (
        <Card>
          <CardHeader>
            <CardTitle>No workspace yet</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <p className="text-muted-foreground text-sm">
              What do you want to learn? Create your own private learning workspace built
              around your goal. You&apos;ll start with a short diagnostic assessment, then get
              a knowledge map and curriculum generated just for you.
            </p>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="goal-text" className="text-sm font-medium">
                Your learning goal
              </label>
              <Textarea
                id="goal-text"
                placeholder="e.g. Learn classical guitar well enough to play at a friend's wedding in 3 months"
                value={goalText}
                maxLength={MAX_GOAL_LENGTH}
                onChange={(event) => setGoalText(event.target.value)}
              />
            </div>
            <Button onClick={handleCreate} disabled={busy || !goalTextValid} className="w-fit">
              {busy ? "Creating..." : "Create my workspace"}
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {state.kind === "has_workspace" ? (
        <Card>
          <CardHeader>
            <CardTitle>You already have a workspace</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex gap-3">
              {state.assessmentInProgressId ? (
                <Button
                  onClick={() =>
                    router.replace(`/assessment/live/${state.assessmentInProgressId}`)
                  }
                  className="w-fit"
                >
                  Continue my assessment
                </Button>
              ) : (
                <Button onClick={() => router.replace(`/dashboard/${state.runId}`)} className="w-fit">
                  Go to my dashboard
                </Button>
              )}
            </div>

            <div className="border-border/60 flex flex-col gap-3 border-t pt-4">
              <p className="text-muted-foreground text-sm">
                Want to start over with a different goal? Resetting replaces your workspace
                with a fresh one and cannot be undone.
              </p>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="reset-goal-text" className="text-sm font-medium">
                  New learning goal
                </label>
                <Textarea
                  id="reset-goal-text"
                  placeholder="e.g. Learn classical guitar well enough to play at a friend's wedding in 3 months"
                  value={resetGoalText}
                  maxLength={MAX_GOAL_LENGTH}
                  onChange={(event) => setResetGoalText(event.target.value)}
                />
              </div>
              <Button
                variant="outline"
                onClick={handleReset}
                disabled={busy || !resetGoalTextValid}
                className="w-fit"
              >
                {busy ? "Resetting..." : "Reset my workspace"}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
