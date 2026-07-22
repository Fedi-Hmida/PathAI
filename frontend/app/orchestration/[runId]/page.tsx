"use client";

import * as React from "react";
import { useParams } from "next/navigation";

import { RequireAuth } from "@/components/auth/require-auth";
import { PhaseStepper } from "@/components/orchestration/phase-stepper";
import { RunStatusFooter } from "@/components/orchestration/run-status-footer";
import { UnlockingPanel } from "@/components/orchestration/unlocking-panel";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { getOrchestrationRun, getOrchestrationStatus } from "@/lib/api/orchestration";
import { cn } from "@/lib/utils";
import type {
  OrchestrationRunDTO,
  OrchestrationRunStatus,
  OrchestrationStatus,
  OrchestrationStatusResponse,
} from "@/lib/types/orchestration";

type LoadState =
  | { kind: "loading" }
  | { kind: "not_found" }
  | { kind: "invalid_id" }
  | { kind: "ready"; run: OrchestrationRunDTO }
  | { kind: "error"; message: string };

const RUN_STATUS_CONFIG: Record<OrchestrationRunStatus, { label: string; className: string }> = {
  created: { label: "Queued", className: "bg-surface-sunken text-tertiary" },
  in_progress: { label: "Running", className: "bg-brand-tint text-brand" },
  requires_input: { label: "Needs input", className: "bg-warning-tint text-warning" },
  completed: { label: "Completed", className: "bg-success-tint text-success" },
  completed_with_warnings: {
    label: "Completed with warnings",
    className: "bg-success-tint text-success",
  },
  failed: { label: "Failed", className: "bg-danger-tint text-danger" },
};

const POLL_INTERVAL_MS = 2000;

function isTerminalRunStatus(status: OrchestrationRunStatus): boolean {
  return status === "completed" || status === "completed_with_warnings" || status === "failed";
}

function isTerminalStatus(status: OrchestrationStatus): boolean {
  return status === "completed" || status === "failed" || status === "cancelled";
}

export default function OrchestrationRunPage() {
  return (
    <RequireAuth>
      <OrchestrationRunView />
    </RequireAuth>
  );
}

function OrchestrationRunView() {
  const params = useParams<{ runId: string }>();
  const runId = params.runId;
  const [loadedRunId, setLoadedRunId] = React.useState(runId);
  const [state, setState] = React.useState<LoadState>({ kind: "loading" });

  // Reset to loading during render when runId changes, same pattern as the
  // Dashboard page (React's documented way to reset state on a changed param).
  if (runId !== loadedRunId) {
    setLoadedRunId(runId);
    setState({ kind: "loading" });
  }

  const pollTimeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollTokenRef = React.useRef(0);
  const lastStatusRef = React.useRef<OrchestrationStatusResponse | null>(null);

  const stopPolling = React.useCallback(() => {
    pollTokenRef.current += 1;
    if (pollTimeoutRef.current !== null) {
      clearTimeout(pollTimeoutRef.current);
      pollTimeoutRef.current = null;
    }
  }, []);

  // Polls the lightweight /status endpoint every 2s (MAIN.md §18.6). Only
  // when current_node/status/requires_user_input actually change does it
  // fetch the full run (which alone carries completed_nodes/failed_nodes/
  // node_events the stepper needs) — status alone can't drive the stepper.
  const startPolling = React.useCallback(
    (currentRunId: string) => {
      stopPolling();
      const token = pollTokenRef.current;
      lastStatusRef.current = null;

      const tick = () => {
        getOrchestrationStatus(currentRunId)
          .then(async (status) => {
            if (pollTokenRef.current !== token) {
              return;
            }
            const previous = lastStatusRef.current;
            const changed =
              previous === null ||
              previous.current_node !== status.current_node ||
              previous.status !== status.status ||
              previous.requires_user_input !== status.requires_user_input;
            lastStatusRef.current = status;

            if (changed) {
              const fullRun = await getOrchestrationRun(currentRunId);
              if (pollTokenRef.current !== token) {
                return;
              }
              setState({ kind: "ready", run: fullRun });
            }

            if (!isTerminalStatus(status.status) && pollTokenRef.current === token) {
              pollTimeoutRef.current = setTimeout(tick, POLL_INTERVAL_MS);
            }
          })
          .catch(() => {
            if (pollTokenRef.current === token) {
              pollTimeoutRef.current = setTimeout(tick, POLL_INTERVAL_MS);
            }
          });
      };

      pollTimeoutRef.current = setTimeout(tick, POLL_INTERVAL_MS);
    },
    [stopPolling]
  );

  React.useEffect(() => {
    let cancelled = false;

    getOrchestrationRun(runId)
      .then((run) => {
        if (cancelled) {
          return;
        }
        setState({ kind: "ready", run });
        if (!isTerminalRunStatus(run.status)) {
          startPolling(runId);
        }
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }
        if (error instanceof ApiError && error.status === 404) {
          setState({ kind: "not_found" });
          return;
        }
        // The backend's RunId type requires a "run_" prefix + pattern
        // (schemas/ids.py); a malformed id fails FastAPI's request
        // validation with 422 before ever reaching the not-found path.
        if (error instanceof ApiError && error.status === 422) {
          setState({ kind: "invalid_id" });
          return;
        }
        const message =
          error instanceof ApiError ? error.message : "Unable to reach the PathAI backend.";
        setState({ kind: "error", message });
      });

    return () => {
      cancelled = true;
      stopPolling();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId]);

  if (state.kind === "loading") {
    return <OrchestrationSkeleton />;
  }

  if (state.kind === "error") {
    return (
      <Alert variant="destructive">
        <AlertTitle>Couldn&apos;t load this run</AlertTitle>
        <AlertDescription>{state.message}</AlertDescription>
      </Alert>
    );
  }

  if (state.kind === "invalid_id") {
    return <p className="text-muted-foreground text-sm">That doesn&apos;t look like a valid run ID.</p>;
  }

  const run = state.kind === "ready" ? state.run : null;
  const notFound = state.kind === "not_found";

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-3">
        <span className="text-tertiary text-[11px] font-semibold tracking-widest uppercase">
          Orchestration run
        </span>
        <p className="text-muted-foreground text-sm">
          <span className="font-mono">{run?.run_id ?? runId}</span>
          {run?.goal_id ? (
            <>
              {" "}
              &middot; goal <span className="font-mono">{run.goal_id}</span>
            </>
          ) : null}
        </p>
        {run ? (
          <Badge className={cn("w-fit rounded-full px-3 py-1.5 text-sm", RUN_STATUS_CONFIG[run.status].className)}>
            {RUN_STATUS_CONFIG[run.status].label}
          </Badge>
        ) : null}
      </div>

      {run ? (
        <div className="flex flex-wrap items-start gap-6">
          <PhaseStepper run={run} />
          <UnlockingPanel run={run} />
        </div>
      ) : null}

      <RunStatusFooter run={run} notFound={notFound} />
    </div>
  );
}

function OrchestrationSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col gap-3">
        <Skeleton className="h-3 w-40" />
        <Skeleton className="h-7 w-28 rounded-full" />
      </div>
      <div className="flex flex-wrap gap-6">
        <Skeleton className="h-[420px] flex-[2_1_520px] min-w-[440px] rounded-2xl" />
        <Skeleton className="h-[420px] w-[280px] rounded-2xl" />
      </div>
    </div>
  );
}
