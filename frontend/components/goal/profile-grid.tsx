import type * as React from "react";

import { DifficultyPips } from "@/components/goal/difficulty-pips";
import { formatConceptLabel } from "@/lib/utils";
import type { DifficultyLevel } from "@/lib/types/curriculum";

export interface ProfileGridProps {
  learnerType: string;
  desiredOutcome: string;
  timeAvailabilityHoursPerWeek: number;
  targetDurationWeeks: number | null;
  hoursPerWeek: number | null;
  difficultyTarget: DifficultyLevel;
}

export function ProfileGrid({
  learnerType,
  desiredOutcome,
  timeAvailabilityHoursPerWeek,
  targetDurationWeeks,
  hoursPerWeek,
  difficultyTarget,
}: ProfileGridProps) {
  const showSessionStat = hoursPerWeek !== null && hoursPerWeek !== timeAvailabilityHoursPerWeek;

  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-x-6 gap-y-8">
      <div>
        <GridLabel>Who you are</GridLabel>
        <p className="text-foreground text-[15px] leading-normal">{learnerType}</p>
      </div>

      <div>
        <GridLabel>What success looks like</GridLabel>
        <p className="text-foreground text-pretty text-[17px] leading-relaxed italic">
          {desiredOutcome}
        </p>
      </div>

      <div>
        <GridLabel>Pace</GridLabel>
        <div className="flex flex-wrap gap-2.5">
          <PaceStat value={timeAvailabilityHoursPerWeek} label="hrs/week" />
          <PaceStat value={targetDurationWeeks ?? "—"} label="weeks" />
          {showSessionStat ? (
            <PaceStat value={hoursPerWeek} label="hrs/week (session)" />
          ) : null}
        </div>
      </div>

      <div>
        <GridLabel>Target difficulty</GridLabel>
        <div className="flex items-center gap-2.5">
          <DifficultyPips level={difficultyTarget} />
          <span className="text-foreground text-[13px] font-semibold">
            {formatConceptLabel(difficultyTarget)}
          </span>
        </div>
      </div>
    </div>
  );
}

function GridLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-tertiary mb-2 text-[11px] font-semibold tracking-widest uppercase">
      {children}
    </div>
  );
}

function PaceStat({ value, label }: { value: number | string; label: string }) {
  return (
    <div className="bg-surface-sunken border-border min-w-[92px] rounded-md border px-4 py-2.5">
      <div className="text-foreground font-mono text-xl font-bold tabular-nums">{value}</div>
      <div className="text-tertiary mt-0.5 text-[11px]">{label}</div>
    </div>
  );
}
