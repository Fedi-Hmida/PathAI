import { AlertTriangle, Check, X } from "lucide-react";

import { cn } from "@/lib/utils";
import { NODE_SEQUENCE } from "@/lib/types/orchestration";
import type { NodeName, OrchestrationRunDTO } from "@/lib/types/orchestration";

export type PhaseStatus = "pending" | "running" | "done" | "failed" | "needs_input";

const PHASE_LABELS: Record<NodeName, string> = {
  initialize_run: "Starting your run",
  load_goal: "Reading your goal",
  load_assessment: "Reviewing your diagnostic",
  load_knowledge_map: "Mapping what you know",
  load_curriculum: "Drafting your curriculum",
  load_resources: "Curating resources",
  load_critic_review: "Quality review",
  load_progress: "Setting up progress tracking",
  load_quiz: "Preparing your first quiz",
  load_adaptation: "Checking for plan adjustments",
  load_evaluation: "Final evaluation",
  prepare_dashboard_payload: "Preparing your dashboard",
  complete_run: "Finishing up",
};

const LABEL_COLOR: Record<PhaseStatus, string> = {
  pending: "text-tertiary",
  running: "text-foreground",
  done: "text-foreground",
  failed: "text-danger",
  needs_input: "text-warning",
};

export function derivePhaseStatus(nodeName: string, run: OrchestrationRunDTO): PhaseStatus {
  if (run.failed_nodes.includes(nodeName)) {
    return "failed";
  }
  if (run.completed_nodes.includes(nodeName)) {
    return "done";
  }
  if (run.current_node === nodeName) {
    return run.status === "requires_input" ? "needs_input" : "running";
  }
  return "pending";
}

function isRevisingCurriculum(nodeName: string, status: PhaseStatus, run: OrchestrationRunDTO): boolean {
  return (
    nodeName === "load_curriculum" &&
    status === "running" &&
    run.completed_nodes.includes("load_critic_review")
  );
}

function subtextFor(
  nodeName: string,
  status: PhaseStatus,
  revising: boolean,
  run: OrchestrationRunDTO
): { text: string; tone: "warning" | "danger" } | null {
  if (revising) {
    return { text: "Regenerating after critic review", tone: "warning" };
  }
  if (status === "needs_input") {
    return { text: "Waiting for your input before this step can continue.", tone: "warning" };
  }
  if (status === "failed") {
    const lastError = run.errors[run.errors.length - 1];
    return lastError ? { text: lastError.message, tone: "danger" } : null;
  }
  return null;
}

function PhaseIcon({ status }: { status: PhaseStatus }) {
  if (status === "done") {
    return (
      <div className="bg-success flex size-[17px] flex-none items-center justify-center rounded-full">
        <Check className="size-2.5 text-white" strokeWidth={3} />
      </div>
    );
  }
  if (status === "failed") {
    return (
      <div className="bg-danger flex size-[17px] flex-none items-center justify-center rounded-full">
        <X className="size-2.5 text-white" strokeWidth={3} />
      </div>
    );
  }
  if (status === "needs_input") {
    return (
      <div className="bg-warning flex size-[17px] flex-none items-center justify-center rounded-full">
        <AlertTriangle className="size-2.5 text-white" fill="white" strokeWidth={0} />
      </div>
    );
  }
  if (status === "running") {
    return <div className="bg-brand motion-safe:animate-pulse size-[15px] flex-none rounded-full" />;
  }
  return <div className="border-border bg-card size-[15px] flex-none rounded-full border-2" />;
}

type PhaseStepperProps = {
  run: OrchestrationRunDTO;
};

export function PhaseStepper({ run }: PhaseStepperProps) {
  return (
    <div className="border-border bg-card flex-[2_1_520px] min-w-[440px] rounded-2xl border px-7 py-1 shadow-sm">
      {NODE_SEQUENCE.map((nodeName, index) => {
        const status = derivePhaseStatus(nodeName, run);
        const revising = isRevisingCurriculum(nodeName, status, run);
        const subtext = subtextFor(nodeName, status, revising, run);
        const isFirst = index === 0;
        const isLast = index === NODE_SEQUENCE.length - 1;
        const prevStatus = index > 0 ? derivePhaseStatus(NODE_SEQUENCE[index - 1], run) : null;

        return (
          <div key={nodeName} className="flex gap-4.5">
            <div className="flex w-5 flex-none flex-col items-center">
              <div
                className={cn(
                  "w-0.5 flex-none",
                  isFirst ? "h-0" : "h-3.5",
                  prevStatus === "done" ? "bg-success" : "bg-border"
                )}
              />
              <PhaseIcon status={status} />
              <div
                className={cn(
                  "w-0.5 flex-1",
                  isLast ? "min-h-0" : "min-h-3.5",
                  status === "done" ? "bg-success" : "bg-border"
                )}
              />
            </div>

            <div className="min-w-0 flex-1 py-3.5 pb-5.5">
              <div className="flex flex-wrap items-center gap-2">
                <span className={cn("text-[15px] font-semibold", LABEL_COLOR[status])}>
                  {PHASE_LABELS[nodeName]}
                </span>
                <span className="text-tertiary bg-surface-sunken rounded px-1.5 py-0.5 font-mono text-[11px]">
                  {nodeName}
                </span>
                {revising ? (
                  <span className="bg-warning-tint text-warning rounded-full px-1.5 py-0.5 text-[10.5px] font-bold tracking-wide uppercase">
                    Revising
                  </span>
                ) : null}
              </div>
              {subtext ? (
                <div
                  className={cn(
                    "mt-1 font-mono text-xs leading-relaxed",
                    subtext.tone === "danger" ? "text-danger" : "text-muted-foreground"
                  )}
                >
                  {subtext.text}
                </div>
              ) : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}
