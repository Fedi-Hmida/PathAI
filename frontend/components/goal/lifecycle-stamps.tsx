import { cn } from "@/lib/utils";
import type { GoalStatus } from "@/lib/types/dashboard";

type StampDef = {
  key: GoalStatus;
  label: string;
  rotate: number;
};

const STAMPS: StampDef[] = [
  { key: "created", label: "Created", rotate: -6 },
  { key: "assessment_started", label: "Assessment Started", rotate: 4 },
  { key: "curriculum_generated", label: "Curriculum Generated", rotate: -3 },
  { key: "active", label: "Active", rotate: 5 },
  { key: "completed", label: "Completed", rotate: -4 },
  { key: "failed", label: "Failed", rotate: 3 },
];

// Failure can happen from any earlier stage, so a failed goal still shows
// progress through "active" reached, with only the Failed stamp flagged.
const PROGRESSION_ORDER: GoalStatus[] = [
  "created",
  "assessment_started",
  "curriculum_generated",
  "active",
  "completed",
];

export interface LifecycleStampsProps {
  status: GoalStatus;
}

export function LifecycleStamps({ status }: LifecycleStampsProps) {
  const progressIndex =
    status === "failed" ? PROGRESSION_ORDER.indexOf("active") : PROGRESSION_ORDER.indexOf(status);

  return (
    <div className="flex flex-wrap justify-center gap-3.5">
      {STAMPS.map((stamp, index) => {
        const isFailedStamp = stamp.key === "failed";
        const reached = isFailedStamp ? status === "failed" : index <= progressIndex;

        return (
          <div
            key={stamp.key}
            style={{ transform: `rotate(${stamp.rotate}deg)` }}
            className={cn(
              "flex size-16 flex-none items-center justify-center rounded-full p-1 text-center text-[8px] leading-tight font-bold tracking-wide uppercase",
              reached
                ? isFailedStamp
                  ? "border-2 border-warning text-warning"
                  : "border-2 border-brand text-brand"
                : "border-border text-tertiary border-dashed"
            )}
          >
            {stamp.label}
          </div>
        );
      })}
    </div>
  );
}
