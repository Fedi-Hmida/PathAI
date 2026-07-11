import Link from "next/link";
import { AlertTriangle, ArrowRight, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { DEMO_RUN_ID } from "@/lib/types/orchestration";
import type { OrchestrationRunDTO } from "@/lib/types/orchestration";

type RunStatusFooterProps = {
  runId: string;
  run: OrchestrationRunDTO | null;
  notFound: boolean;
  triggering: boolean;
  onTrigger: () => void;
};

export function RunStatusFooter({ runId, run, notFound, triggering, onTrigger }: RunStatusFooterProps) {
  const isDemoRun = runId === DEMO_RUN_ID;

  if (notFound) {
    if (!isDemoRun) {
      return <p className="text-muted-foreground text-sm">Run not found.</p>;
    }
    return (
      <div className="flex flex-col items-start gap-3">
        <p className="text-muted-foreground text-sm">
          No run yet for the PathAI demo goal. This starts the canonical demo pipeline only
          &mdash; the backend doesn&apos;t yet support triggering a run for a custom goal.
        </p>
        <Button size="lg" onClick={onTrigger} disabled={triggering}>
          {triggering ? "Starting…" : "Run demo pipeline"}
        </Button>
      </div>
    );
  }

  if (run === null) {
    return null;
  }

  if (run.status === "requires_input") {
    return (
      <div className="border-warning bg-warning-tint flex items-center gap-4 rounded-2xl border px-5 py-4">
        <AlertTriangle className="text-warning size-4 flex-none" />
        <p className="text-foreground text-[13.5px]">
          Waiting for your input before this run can continue.
        </p>
      </div>
    );
  }

  if (run.status === "completed" || run.status === "completed_with_warnings") {
    return (
      <div className="flex flex-wrap items-center gap-3">
        <Button size="lg" asChild>
          <Link href={`/dashboard/${run.run_id}`}>
            View your dashboard
            <ArrowRight className="size-4" />
          </Link>
        </Button>
        {isDemoRun ? (
          <Button size="lg" variant="secondary" onClick={onTrigger} disabled={triggering}>
            <RefreshCw className="size-4" />
            {triggering ? "Starting…" : "Re-run demo pipeline"}
          </Button>
        ) : null}
      </div>
    );
  }

  if (run.status === "failed") {
    const lastError = run.errors[run.errors.length - 1];
    return (
      <div className="border-danger bg-danger-tint flex flex-col gap-3.5 rounded-2xl border px-5 py-4.5">
        <p className="text-foreground text-[13.5px] leading-relaxed">
          {lastError?.message ?? "This run failed."}
        </p>
        <div className="flex flex-wrap items-center gap-4">
          {isDemoRun ? (
            <Button variant="destructive" onClick={onTrigger} disabled={triggering}>
              <RefreshCw className="size-4" />
              {triggering ? "Retrying…" : "Retry"}
            </Button>
          ) : null}
          <Link
            href={`/dashboard/${run.run_id}`}
            className="text-muted-foreground text-sm underline underline-offset-4"
          >
            View dashboard
          </Link>
        </div>
      </div>
    );
  }

  return <p className="text-muted-foreground text-sm">This usually takes under a minute.</p>;
}
