import Link from "next/link";
import { AlertTriangle, ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { OrchestrationRunDTO } from "@/lib/types/orchestration";

type RunStatusFooterProps = {
  run: OrchestrationRunDTO | null;
  notFound: boolean;
};

export function RunStatusFooter({ run, notFound }: RunStatusFooterProps) {
  if (notFound) {
    return (
      <div className="flex flex-col items-start gap-3">
        <p className="text-muted-foreground text-sm">Run not found.</p>
        <Link href="/workspace" className="text-sm underline underline-offset-4">
          Create a workspace to get started
        </Link>
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
        <Link
          href={`/dashboard/${run.run_id}`}
          className="text-muted-foreground text-sm underline underline-offset-4"
        >
          View dashboard
        </Link>
      </div>
    );
  }

  return <p className="text-muted-foreground text-sm">This usually takes under a minute.</p>;
}
