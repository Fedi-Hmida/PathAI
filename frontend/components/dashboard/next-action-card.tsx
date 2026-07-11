import { Target } from "lucide-react";

import type { ProgressSummary } from "@/lib/types/dashboard";

type NextActionCardProps = {
  progressSummary: ProgressSummary | null;
};

export function NextActionCard({ progressSummary }: NextActionCardProps) {
  const label = progressSummary?.next_action_label ?? null;
  const reason = progressSummary?.next_action_reason ?? null;

  return (
    <div className="border-brand-border bg-brand-tint flex flex-1 flex-col gap-4 rounded-2xl border p-6 shadow-sm">
      <span className="text-brand text-[11px] font-semibold tracking-widest uppercase">
        Next action
      </span>
      {label ? (
        <div className="flex items-start gap-3">
          <div className="bg-card flex size-8.5 flex-none items-center justify-center rounded-full">
            <Target className="text-brand size-4" />
          </div>
          <div>
            <div className="font-goal text-foreground text-[19px] leading-snug font-medium">
              {label}
            </div>
            {reason ? (
              <div className="text-muted-foreground mt-1.5 text-[13px] leading-relaxed">
                {reason}
              </div>
            ) : null}
          </div>
        </div>
      ) : (
        <p className="text-muted-foreground text-sm">
          Nothing scheduled yet — check back once the curriculum and progress data are ready.
        </p>
      )}
    </div>
  );
}
