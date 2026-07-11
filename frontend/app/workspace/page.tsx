"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { RequireAuth } from "@/components/auth/require-auth";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  | { kind: "has_workspace"; runId: string }
  | { kind: "error"; message: string };

function WorkspaceView() {
  const router = useRouter();
  const [state, setState] = React.useState<ViewState>({ kind: "loading" });
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    let cancelled = false;
    getMyWorkspace()
      .then((workspace) => {
        if (cancelled) {
          return;
        }
        setState(workspace ? { kind: "has_workspace", runId: workspace.run_id } : { kind: "empty" });
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        const message = error instanceof ApiError ? error.message : "Unable to reach the PathAI backend.";
        setState({ kind: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleCreate() {
    setBusy(true);
    try {
      const workspace = await createMyWorkspace();
      router.replace(`/dashboard/${workspace.run_id}`);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Unable to reach the PathAI backend.";
      setState({ kind: "error", message });
    } finally {
      setBusy(false);
    }
  }

  async function handleReset() {
    setBusy(true);
    try {
      const workspace = await resetMyWorkspace();
      router.replace(`/dashboard/${workspace.run_id}`);
    } catch (error) {
      const message = error instanceof ApiError ? error.message : "Unable to reach the PathAI backend.";
      setState({ kind: "error", message });
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
              curriculum. It belongs only to you.
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
              <Button onClick={() => router.replace(`/dashboard/${state.runId}`)} className="w-fit">
                Go to my dashboard
              </Button>
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
