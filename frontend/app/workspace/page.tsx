"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { RequireAuth } from "@/components/auth/require-auth";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getMyAssessment, startAssessment } from "@/lib/api/assessment";
import { ApiError } from "@/lib/api/client";
import { createMyWorkspace, getMyWorkspace, resetMyWorkspace } from "@/lib/api/workspace";

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
    setBusy(true);
    try {
      await createMyWorkspace();
      await goToLiveAssessment();
    } catch (error) {
      setState({ kind: "error", message: errorMessage(error) });
    } finally {
      setBusy(false);
    }
  }

  async function handleReset() {
    setBusy(true);
    try {
      await resetMyWorkspace();
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
              Create your own private learning workspace, seeded from the PathAI demo
              curriculum. It belongs only to you. You&apos;ll start with a short diagnostic
              assessment.
            </p>
            <Button onClick={handleCreate} disabled={busy} className="w-fit">
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
            <p className="text-muted-foreground text-sm">
              Resetting replaces your workspace with a fresh copy and cannot be undone.
            </p>
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
              <Button variant="outline" onClick={handleReset} disabled={busy} className="w-fit">
                {busy ? "Resetting..." : "Reset my workspace"}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
